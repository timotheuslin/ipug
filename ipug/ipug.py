#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, line-too-long, too-many-nested-blocks, too-many-branches, too-many-locals
#

"""
PUG: 'Pug, the UDK Guidedog', or 'the Programmer's UDK Guide'.
A front-end to build the UDK driver(s) with only .C source files and a .PY as the config file.

(c) 2019 Timothy Lin <timothy.gh.lin@gmail.com>, BSD 3-Clause License.

Prerequisites:
1. Python 2.7.10+ or Python 3.7.0+
2. git 2.19.0+

Generic prerequisites for the UDK build:
0. Ref. https://github.com/tianocore/tianocore.github.io/wiki/Getting%20Started%20with%20EDK%20II
        Xcode: https://github.com/tianocore/tianocore.github.io/wiki/Xcode
1. nasm (2.0 or above)
2. iasl (version 2018xxxx or later)
3. GCC(Posix) or MSVC(Windows)
4. build-essential uuid-dev (Posix)
5. pip2 install future (Python 2.7.x)
6. motc (Xcode)

Tool installation for any Debian Based Linux:
1. sudo apt update & sudo apt install nasm iasl build-essential uuid-dev

TODO:
- The driver's specific settings can reside in its major .C file for self-contained purpose. -- i.e. relocate them from config.py
- keyword list of the supported section names of DSC and INF.
- X64/IA32/ARM/... section differentiation.
- automate the tool-chain for Windows/Linux/Mac.

"""

from __future__ import print_function
from __future__ import absolute_import

__all__ = ['build', 'build_basetools', 'run', 'setup_codetree']

import os
import sys
import time
import shutil
import threading
import subprocess
import multiprocessing

from ipug import config

sys.dont_write_bytecode = True      # To inhibit the creation of .pyc file

VERBOSE_LEVEL = 1
UDKBUILD_MAKETOOL = 'nmake' if (os.name == 'nt') else 'make'
UDKBUILD_COMMAND_JOINTER = '&' if (os.name == 'nt') else ';'

default_pug_signature = '#\n# Do not edit this file.\n# It is automatically created by PUG.\n#\n'


def pwdpopd(target_dir=''):
    """pwd | popd
    when a directory is assigned, (1) the current directory is pushed to the stack, (2) chdir() to that assigned directory.
    when a directory is not assigned, (1) a directory is popped from the stack, (2) chdir() to that popped directory.
    It's the caller's responsibility to maintain the stack's balance.
    """
    if target_dir:
        pwdpopd.pushd += [os.getcwd()]
    else:
        if pwdpopd.pushd:
            target_dir = pwdpopd.pushd.pop()
    if target_dir:
        os.chdir(target_dir)
pwdpopd.pushd = []


def bowwow(msg):
    """display some tagged progress messages when iPug is running."""
    pugsay = 'PUG: '
    if msg.startswith('\n'):
        print('\n')
        msg = msg[1:]
    msg = msg.replace('\n', '\n{}'.format(pugsay))
    print('{0}{1}'.format(pugsay, str(msg)))


def abs_path(sub_dir, base_dir):
    """return an absolute path."""
    return sub_dir if os.path.isabs(sub_dir) else os.path.join(base_dir, sub_dir)


def write_file(path, content, signature=''):
    """update a platform's dsc file content.
    - create the folder when it does not exist.
    - skip write attempt when the contents are identical"""

    if isinstance(content, (list, tuple)):
        content = '\n'.join(content)
        if not content.endswith('\n'):
            content += '\n'
    if signature:
        content = signature + content
    path_dir = os.path.dirname(path)
    content0 = ''
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
    else:
        if os.path.exists(path):
            with open(path, 'r') as pf:
                content0 = pf.read()
            if content0 == content:
                return
    with open(path, 'w') as pf:
        pf.write(content)


def conf_files(files, dest_conf_dir, verbose=False):
    """Ref. BaseTools/BuildEnv for build_rule.txt , tools_def.txt and target.txt"""
    dest_conf_dir = os.path.abspath(dest_conf_dir)
    if not os.path.exists(dest_conf_dir):
        os.makedirs(dest_conf_dir)
    os.environ['CONF_PATH'] = dest_conf_dir
    src_conf_dir = os.path.join(os.environ.get('EDK_TOOLS_PATH', os.path.join(os.environ['WORKSPACE'], 'BaseTools')), 'Conf')
    for f in files:
        src_conf_path = os.path.join(src_conf_dir, '%s.template' % f)
        dest_conf_path = os.path.join(dest_conf_dir, '%s.txt' % f)
        if verbose:
            bowwow('Copy %s\nTo   %s' % (src_conf_path, dest_conf_path))
        shutil.copyfile(src_conf_path, dest_conf_path)


def gen_section(items, override=None, section='', sep='=', ident=0):
    """generate a section's content"""
    ret_list = []
    if section:
        ret_list += ['\n%s[%s]' % (' '*ident*2, section)]
    if items:
        if isinstance(items, (tuple, list)) or (override in {list, tuple}):
            for d in items:
                if d:
                    if isinstance(d, (list, tuple)):
                        ret_list += ['%s%s' % (' '*(ident+1)*2, sep.join(d))]
                    else:
                        ret_list += ['%s%s' % (' '*(ident+1)*2, str(d))]
        elif isinstance(items, dict):
            ret_list += ['%s%s %s %s' % (' '*(ident+1)*2, str(d), sep, str(items[d])) for d in sorted(items) if d]
    return ret_list


def gen_target_txt(target_txt):
    """generate the content of Conf/target.txt"""
    tt = []
    for s in sorted(target_txt):
        if s.isupper():
            tt += ['%s = %s' % (s, target_txt[s])]
    write_file(target_txt['path'], tt)


def run(Command, WorkingDir='.', verbose=False):
    """A derivative of UDK's BaseTools/build/build.py::launch_command

        returns
        [0] - error code
        [1] - buffered stdout content, list
        [2] - buffered stderr content, list
    """
    stdout_buffer = []
    stderr_buffer = []

    def ReadMessage(From, To, ExitFlag):
        """read message fro stream"""
        while True:
            Line = From.readline()
            if Line:
                To(Line.rstrip())
            if not Line or ExitFlag.isSet():
                break

    def __logger(msg, buf):
        if isinstance(msg, bytes):
            msg = msg.decode('utf-8')
        if verbose:
            print('%s' % msg)
        buf += [msg]

    def logger_stdout(msg):
        """print message from stdout"""
        __logger(msg, stdout_buffer)

    def logger_stderr(msg):
        """print message from stderr"""
        __logger(msg, stderr_buffer)

    if isinstance(Command, (list, tuple)):
        Command = ' '. join(Command)

    WorkingDir = os.path.abspath(WorkingDir)
    pwdpopd(WorkingDir)
    bowwow('Run: [%s] @ [%s]' % (Command, WorkingDir))

    Proc = EndOfProcedure = StdOutThread = StdErrThread = None
    _stdout = sys.stdout if verbose else subprocess.PIPE
    _stderr = sys.stderr if verbose else subprocess.PIPE
    Proc = subprocess.Popen(Command, stdout=_stdout, stderr=_stderr, env=os.environ, cwd=WorkingDir, bufsize=-1, shell=True)
    if not verbose:
        EndOfProcedure = threading.Event()
        EndOfProcedure.clear()
        if Proc.stdout:
            StdOutThread = threading.Thread(target=ReadMessage, args=(Proc.stdout, logger_stdout, EndOfProcedure))
            StdOutThread.setName('STDOUT-Redirector')
            StdOutThread.setDaemon(False)
            StdOutThread.start()
        if Proc.stderr:
            StdErrThread = threading.Thread(target=ReadMessage, args=(Proc.stderr, logger_stderr, EndOfProcedure))
            StdErrThread.setName('STDERR-Redirector')
            StdErrThread.setDaemon(False)
            StdErrThread.start()
        # waiting for program exit
    Proc.wait()

    return_code = -1
    if Proc:
        if Proc.stdout and StdOutThread:
            StdOutThread.join()
        if Proc.stderr and StdErrThread:
            StdErrThread.join()
        return_code = Proc.returncode
    pwdpopd()
    return return_code, stdout_buffer, stderr_buffer


def print_run_result(r, prompt=''):
    """print the stdour & stderr when return code is non-zero."""
    if r[0]:
        s1 = '\n'.join(r[1])
        s2 = '\n'.join(r[2])
        if s1 or s2:
            bowwow('{0}{1}'.format(prompt, '\n'.join([s1, 'STDERR:', s2])))
    else:
        bowwow('{0}Success'.format(prompt))
    return r[0]


def locate_nasm():
    """Try to locate the nasm's installation directory. For Windows only."""
    for d in [
            'C:\\Program Files\\NASM\nasm.exe',
            'C:\\Program Files (x86)\\NASM\nasm.exe',
            os.environ.get('LOCALAPPDATA', '') + '\\bin\\NASM\\nasm.exe',
            'C:\\NASM\\nasm.exe',
    ]:
        if os.path.exists(d):
            return os.path.dirname(d)
    return ''


def env_var(k, v):
    """Setup environment variable"""
    k0 = k[0]
    k1 = k[1:]
    if v[0] == '$':             # marco from os.environ
        v = os.environ.get(v[1:], '')
    if k0 in {'+', '*'}:
        try:
            ex = ''
            if k0 == '+':       # append
                ex = '%s%s%s' % (os.environ[k1], os.pathsep, v)
            elif k0 == '*':     # prepend
                ex = '%s%s%s' % (v, os.pathsep, os.environ[k1])
            os.environ[k1] = ex
        except KeyError:
            os.environ[k1] = v
    elif k0 == '=':             # conditional assignment
        if k1 not in os.environ:
            os.environ[k1] = v
    else:                       # unconditional assignment
        os.environ[k] = v


def setup_env_vars(workspace, codetree):
    """Setup environment variables"""
    env_var('=WORKSPACE', os.path.abspath(workspace))
    udk_home = config.CODETREE['edk2']['path']
    env_var('=UDK_ABSOLUTE_DIR', os.path.abspath(udk_home))
    env_var('=EDK_TOOLS_PATH', os.path.join(os.environ['UDK_ABSOLUTE_DIR'], 'BaseTools'))
    env_var('=CONF_PATH', os.path.join(os.environ['WORKSPACE'], 'Conf'))
    env_var('=BASE_TOOLS_PATH', '$EDK_TOOLS_PATH')
    env_var('=PYTHONPATH', os.path.join(os.environ['EDK_TOOLS_PATH'], 'Source', 'Python'))
    env_var('=EDK_TOOLS_PATH_BIN', os.path.join(os.environ['EDK_TOOLS_PATH'], 'BinWrappers', 'WindowsLike' if os.name == 'nt' else 'PosixLike'))

    if os.name == 'nt':
        env_var('*PATH', os.path.join(os.environ['EDK_TOOLS_PATH'], 'Bin', 'Win32'))
        env_var('=PYTHON_HOME', os.path.dirname(sys.executable))
        env_var('=PYTHONHOME', os.path.dirname(sys.executable))
        nasm_path = locate_nasm()
        if nasm_path:
            env_var('=NASM_PREFIX', nasm_path + os.sep)
        env_var('=PYTHON_COMMAND', 'python')
    env_var('*PATH', '$EDK_TOOLS_PATH_BIN')
    env_var('+PACKAGES_PATH', '$UDK_ABSOLUTE_DIR')
    env_var('+PACKAGES_PATH', os.getcwd())
    for c in codetree:
        if c == 'edk2':
            continue
        if codetree[c].get('multiworkspace', False):
            env_var('+PACKAGES_PATH', codetree[c]['path'])

    bowwow('WORKSPACE      = %s' % os.environ['WORKSPACE'])
    bowwow('PACKAGES_PATH  = %s' % os.environ['PACKAGES_PATH'])
    bowwow('EDK_TOOLS_PATH = %s' % os.environ['EDK_TOOLS_PATH'])
    bowwow('CONF_PATH      = %s' % os.environ['CONF_PATH'])


def build_basetools(verbose=0):
    """build the C-lang executables in Basetools.
    Use: sys.argv[1]: 'clean' """
    home_dir = os.environ['EDK_TOOLS_PATH']
    cmds = [
        UDKBUILD_MAKETOOL,
    ]
    if UDKBUILD_MAKETOOL == 'make':
        cmds += [
            '--jobs', '%d' % multiprocessing.cpu_count()
        ]
    if 'cleanall' in sys.argv[1:]:
        cmds += ['clean']
    r = run(cmds, home_dir, verbose=verbose)
    return print_run_result(r, 'build_basetools(): ')


def apply_patch(codetree, workspace):
    """apply patches to the code tree."""
    r0, r1, r2 = 0, [], []
    for c in codetree.values():
        cPatch = c.get('patch', None)
        if cPatch is None:
            continue
        s = run(cPatch, workspace, verbose=False)
        r0 |= s[0]
        r1 += s[1]
        r2 += s[2]
    return print_run_result((r0, r1, r2), 'apply_patch(): ')


def setup_codetree(codetree):
    """pull the udk code tree when it does not locally/correctly exist.
        1. git clone
        2. git checkout tag/branch/master"""

    def _get_code(node):
        """get code using git clone/checkout"""
        r = 0, [], []
        local_dir = node['path']
        dot_git = os.path.join(local_dir, '.git')
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        nsource = node.get('source', None)
        if nsource is None:
            return r
        nsource_url = nsource.get('url', None)
        if nsource_url is None:
            return r
        nsource_signature = nsource.get('signature', 'master')
        if not nsource_signature:
            nsource_signature = 'master'
        if not os.path.exists(dot_git):
            r = run(['git', 'clone', nsource_url, local_dir], local_dir, verbose=True)
            if r[0]:
                return r
        # bugbug
        #r = run(['git', 'checkout', 'master'], local_dir, verbose=True)
        #if r[0]:
        #    return r
        #r = run(['git', 'pull'], local_dir, verbose=True)
        #if r[0]:
        #    return r
        
        r = run(['git', 'checkout', nsource_signature], local_dir, verbose=True)
        if r[0]:
            return r
        if node.get('recursive', ''):
            r = run(['git', 'submodule update --init --recursive'], local_dir, verbose=True)
        return r

    r0, r1, r2 = _get_code(codetree['edk2'])
    for c in codetree:
        if c == 'edk2':
            continue
        s = _get_code(codetree[c])
        r0 |= s[0]
        r1 += s[1]
        r2 += s[2]
    return print_run_result((r0, r1, r2), 'setup_codetree(): ')


def platform_dsc(platform, components, workspace):
    """generate a platform's dsc file."""

    dsc_path = abs_path(platform['path'], workspace)
    bowwow('PLATFORM_DSC = %s' % dsc_path)
    if not platform.get('update', False):
        return
    sections = ['Defines', 'Components']
    overrides = {'LibraryClasses', 'PcdsFixedAtBuild'}  # , 'BuildOptions'}
    pfile = []
    for s in sections:
        if s == 'Components':
            pfile += gen_section(None, section=s)
            for compc in components:
                pfile += ['  %s' % compc['path']]
                in_override = False
                ovs = overrides.intersection(set(compc.keys()))
                for ov in ovs:
                    # print('Override: %s' % ov)
                    if not in_override:
                        pfile[-1] += ' {'
                        in_override = True
                    pfile += ['    <%s>' % ov]
                    sep = '|' if ov in {'LibraryClasses', 'PcdsFixedAtBuild'} else '='
                    for d in compc[ov]:
                        if d and d[0]:
                            pfile += ['      %s %s %s' % (d[0], sep, d[1])]
                if in_override:
                    pfile += ['  }']
        else:
            pfile += gen_section(platform[s], section=s)
    write_file(dsc_path, pfile, default_pug_signature)


def component_inf(components, workspace):
    """generate INF files of components."""
    sections = [
        'Sources', 'Packages', 'LibraryClasses', 'Protocols', 'Ppis',
        'Guids', 'FeaturePcd', 'Pcd', 'BuildOptions', 'Depex', 'UserExtensions',
    ]
    for comp in components:
        cfile = []
        inf_path = abs_path(comp.get('path', ''), workspace)
        bowwow('COMPONENT: %s' % inf_path)
        if not comp.get('update', False):
            continue
        defines = comp.get('Defines', '')
        if not defines:
            raise Exception('INF must contain [Defines] section.')
        cfile += gen_section(defines, section='Defines')
        for s in comp:
            s0 = s.split('.')[0]
            if s0 not in sections:
                continue
            if s0 == 'LibraryClasses':
                cfile += gen_section([v[0] for v in comp[s] if v[0] != 'NULL'], section=s, override=list)
            else:
                cfile += gen_section(comp[s], section=s)
        write_file(inf_path, cfile, default_pug_signature)


def build():
    """0. prepare the UDK code tree.
       1. setup environment variables.
       2. build C-lang executables in BaseTools.
       3. UDK build."""

    workspace = os.path.abspath(config.WORKSPACE['path'])
    # udk_home = os.path.abspath(config.CODETREE['edk2']['path'])

    r = setup_codetree(config.CODETREE)
    if r:
        bowwow('setup_codetree(0) returns: %s' % str(r))
        bowwow('Unable to setup the UDK code tree correctly.')
        bowwow('Please check the access premission or the sanity of the external folder(s).')
        return r
    r = apply_patch(config.CODETREE, workspace)
    if r:
        bowwow('apply_patch() returns: %s' % str(r))
        bowwow('The path is not applied successfully.')
        bowwow('Maybe the patch has been applied before. Ignoring the error.\n')
        # return r

    setup_env_vars(workspace, config.CODETREE)
    conf_files(['build_rule', 'tools_def', 'target'], config.WORKSPACE['conf_path'], VERBOSE_LEVEL > 1)
    gen_target_txt(config.TARGET_TXT)

    r = build_basetools(verbose=(VERBOSE_LEVEL > 1))
    if r:
        return r

    cPlatform = getattr(config, 'PLATFORM', None)
    cComponent = getattr(config, 'COMPONENT', None)
    if cPlatform and cComponent:
        platform_dsc(cPlatform, cComponent, workspace)
    if cComponent:
        component_inf(cComponent, workspace)

    cmds = []
    if os.name == 'nt':
        cmds += [
            os.path.join(os.environ['EDK_TOOLS_PATH'], 'set_vsprefix_envs.bat'), UDKBUILD_COMMAND_JOINTER,
        ]
    cmds += [
        'build',
        '-n', '%d' % multiprocessing.cpu_count(),
        '-N',                                       # -N, --no-cache        Disable build cache mechanism
    ]

    cmds += sys.argv[1:]
    r = run(cmds, os.environ['WORKSPACE'], verbose=VERBOSE_LEVEL)
    return print_run_result(r, 'build(): ')


def main():
    """main"""
    if config.project is None:
        bowwow('Ingoring the missing project.py.')
    start_time = time.time()
    ret = build()
    elapsed_time = time.gmtime(int(round(time.time() - start_time)))
    elapsed_time_str = time.strftime('%H:%M:%S', elapsed_time)
    if elapsed_time.tm_yday > 1:
        elapsed_time_str += ', %d day(s)' % (elapsed_time.tm_yday - 1)
    bowwow("\nPug's running elapsed time: %s" % elapsed_time_str)
    return ret


if __name__ == '__main__':
    sys.exit(main())
