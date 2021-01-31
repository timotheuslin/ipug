#
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, line-too-long, too-many-nested-blocks, too-many-branches, too-many-locals
#
# (c) 2019-2021 Timothy Lin <timothy.gh.lin@gmail.com>, BSD 3-Clause License.
#

"""
The basic/default configuration file for PUG.
"""

__all__ = ['dump_config', 'dump_env_vars', 'WORKSPACE', 'CODETREE', 'TARGET_TXT', 'PLATFORM', 'COMPONENT', 'VERBOSE_THRESHOLD']

import os
import sys

sys.dont_write_bytecode = True      # inhibit the creation of .pyc file
VERBOSE_THRESHOLD = 1               # the bigger number, the higher threshold, the less messages being displayed

DEFAULT_GCC_TAG = 'GCC5'
DEFAULT_EDK2_TAG = os.environ.get('EDK2_TAG', 'edk2-stable202008')
DEFAULT_MSVC_TAG = os.environ.get('MSVC_TAG', 'VS2017')
DEFAULT_EDK2_REPO = os.environ.get('EDK2_REPO', 'https://github.com/tianocore/edk2.git')
DEFAULT_XCODE_TAG = 'XCODE5'
DEFAULT_TARGET_ARCH = os.environ.get('TARGET_ARCH', 'X64')              # 'IA32', 'X64', 'IA32 X64'
DEFAULT_BUILD_TARGET = os.environ.get('BUILD_TARGET', 'RELEASE')        # 'DEBUG', 'NOOPT', 'RELEASE', 'RELEASE DEBUG'
DEFAULT_BUILD_COMMAND = ''
DEFAULT_WORKSPACE_DIR = os.environ.get('WORKSPACE', os.getcwd())
DEFAULT_ACTIVE_PLATFORM = os.environ.get('ACTIVE_PLATFORM', '')
DEFAULT_PATH_APPEND_SIGNATURE = False

DEFAULT_UDK_DIR = os.environ.get('UDK_DIR', os.path.join(os.path.expanduser('~'), '.cache', 'pug', DEFAULT_EDK2_TAG))

CODETREE = {}
PLATFORM = {}
WORKSPACE = {}
COMPONENT = {}
TARGET_TXT = {}

project = None
project_py = 'project.py'

pCODETREE = {}
pPLATFORM = {}
pWORKSPACE = {}
pCOMPONENT = {}
pTARGET_TXT = {}

ORIGINAL_SYS_PATH = sys.path[:]
customized_settings = {}

# assimilate DEFAULT_* from the environment variable space first.
for dv in os.environ:
    if not dv.startswith('DEFAULT_'):
        continue
    customized_settings[dv] = locals()[dv] = os.environ[dv]

try:
    sys.path = [os.getcwd()] + sys.path
    # WARNING: here is actually a potential vulnerability with unbounded privilege propagation when importing a local python file.
    import project
    pCODETREE = getattr(project, 'CODETREE', {})
    pPLATFORM = getattr(project, 'PLATFORM', {})
    pWORKSPACE = getattr(project, 'WORKSPACE', {})
    pCOMPONENT = getattr(project, 'COMPONENT', {})
    pTARGET_TXT = getattr(project, 'TARGET_TXT', {})

    # TODO: eventually, all the all-capital symbols should be merged from project.py.
    # TODO: any "DEFAULT_" symbol exists in project.py but not in this config.py should be an error. (strict mode)
    for dv in dir(project):
        if not dv.startswith('DEFAULT_'):
            continue
        customized_settings[dv] = locals()[dv] = getattr(project, dv)

except ImportError:
    # let the invoker to handle the mess.
    pass

sys.path = ORIGINAL_SYS_PATH

# update the dependent settings after settings of project.py are loaded.
if ('DEFAULT_UDK_DIR' not in customized_settings) and ('DEFAULT_EDK2_TAG' in customized_settings):
    DEFAULT_UDK_DIR = os.environ.get('UDK_DIR', os.path.join(os.path.expanduser('~'), '.cache', 'pug', DEFAULT_EDK2_TAG))

# basic global settings of WORKSPACE. Any relative-path is relative to the WORKSPACE-dir.
WORKSPACE = {
    'path'              : DEFAULT_WORKSPACE_DIR,
    'target'            : DEFAULT_BUILD_TARGET,
    'target_arch'       : DEFAULT_TARGET_ARCH,
    'tool_chain_tag'    : DEFAULT_MSVC_TAG if (os.name == 'nt') else DEFAULT_XCODE_TAG if (sys.platform == 'darwin') else DEFAULT_GCC_TAG,
}

WORKSPACE['conf_path'] = os.environ.get('CONF_PATH', os.path.join(WORKSPACE['path'], 'Build', 'Conf'))

# code tree layout for those remote repository(-ies).
CODETREE = {
    'edk2'              : {
        'source'        : {
            'url'       : DEFAULT_EDK2_REPO,
            'signature' : DEFAULT_EDK2_TAG,
        },
        'recursive'     : True,
        'multiworkspace': True,
    },
}
CODETREE['edk2']['path'] = DEFAULT_UDK_DIR
if DEFAULT_PATH_APPEND_SIGNATURE and CODETREE['edk2']['source'].get('signature', ''):
    CODETREE['edk2']['path'] = os.path.join(CODETREE['edk2']['path'], CODETREE['edk2']['source'].get('signature', ''))

# Conf/target.txt. Ref. BaseTools/Conf/target.template
TARGET_TXT = {
    'path'              : os.path.join(WORKSPACE['conf_path'], 'target.txt'),
    'update'            : True,
    'TOOL_CHAIN_CONF'   : 'tools_def.txt',
    'BUILD_RULE_CONF'   : 'build_rule.txt',
    'TARGET'            : WORKSPACE['target'],
    'TARGET_ARCH'       : WORKSPACE['target_arch'],
    'TOOL_CHAIN_TAG'    : WORKSPACE['tool_chain_tag'],
    'ACTIVE_PLATFORM'   : '',
}
try:
    TARGET_TXT['ACTIVE_PLATFORM'] = getattr(PLATFORM, 'path', '')
except NameError:
    pass

try:
    if ACTIVE_PLATFORM:
        pass
except NameError:
    ACTIVE_PLATFORM = DEFAULT_ACTIVE_PLATFORM

for c in pCODETREE:
    CODETREE[c] = pCODETREE[c]
for c in pPLATFORM:
    PLATFORM[c] = pPLATFORM[c]
for c in pWORKSPACE:
    WORKSPACE[c] = pWORKSPACE[c]
for c in pCOMPONENT:
    COMPONENT[c] = pCOMPONENT[c]
for c in pTARGET_TXT:
    TARGET_TXT[c] = pTARGET_TXT[c]


def dump_config():
    """ dump all essential configuration settings starting with "DEFAULT_"""

    msg = [
        '--',
        'ESSENTIAL CONFIG SETTINGS', '',
        'CODETREE:',        '  %s' % str(CODETREE),   '',
        'PLATFORM:',        '  %s' % str(PLATFORM),   '',
        'WORKSPACE:',       '  %s' % str(WORKSPACE),  '',
        'COMPONENT:',       '  %s' % str(COMPONENT),  '',
        'TARGET_TXT:',      '  %s' % str(TARGET_TXT), '',
        'ACTIVE_PLATFORM:', '  %s' % ACTIVE_PLATFORM, '',
    ]

    msgx = []
    msg += ['scope: os.environ:']
    for dvx in sorted(os.environ):
        if not dvx.startswith('DEFAULT_'):
            continue
        msgx += ['  %s : [%s]' % (dvx, os.environ[dvx])]
    msg += msgx if msgx else ['  (empty)']

    msgx = []
    msg += ['scope: %s:' % project_py]
    for dvx in sorted(dir(project)):
        if not dvx.startswith('DEFAULT_'):
            continue
        msgx += ['  %s : [%s]' % (dvx, getattr(project, dvx))]
    msg += msgx if msgx else ['  (empty)']

    msgx = []
    msg += ['scope: config.globals():']
    for dvx in sorted(globals()):
        if not dvx.startswith('DEFAULT_'):
            continue
        msgx += ['  %s : [%s]' % (dvx, globals()[dvx])]
    msg += msgx if msgx else ['  (empty)']

    msgx = []
    msg += ['scope: config.locals():']
    for dvx in sorted(locals()):
        if not dvx.startswith('DEFAULT_'):
            continue
        msgx += ['  %s : [%s]' % (dvx, locals()[dvx])]
    msg += msgx if msgx else ['  (empty)']
    msg += ['--']
    return '\n'.join(msg)


def dump_env_vars():
    """ dump essential environ variables."""
    msg = [
        '--',
        'ESSENTIAL ENVIRONMENT VARIABLES',
        '%-16s = %s' % ('WORKSPACE', os.environ.get('WORKSPACE', '')),
        '%-16s = %s' % ('PACKAGES_PATH', os.environ.get('PACKAGES_PATH', '')),
        '%-16s = %s' % ('EDK_TOOLS_PATH', os.environ.get('EDK_TOOLS_PATH', '')),
        '%-16s = %s' % ('CONF_PATH', os.environ.get('CONF_PATH', '')),
        '%-16s = %s' % ('UDK_ABSOLUTE_DIR', os.environ.get('UDK_ABSOLUTE_DIR', '')),
    ]
    if os.name == 'nt':
        msg += ['%-16s = %s' % ('PYTHON_COMMAND', os.environ.get('PYTHON_COMMAND', ''))]
        if os.environ.get('NASM_PREFIX', ''):
            msg += ['%-16s = %s' % ('NASM_PREFIX', os.environ.get('NASM_PREFIX', ''))]
    msg += ['%-16s = %s' % ('PATH', os.environ.get('PATH', ''))]
    msg += ['--']
    return '\n'.join(msg)
