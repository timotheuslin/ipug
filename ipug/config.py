#
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, line-too-long, too-many-nested-blocks, too-many-branches, too-many-locals
#
# (c) 2019 Timothy Lin <timothy.gh.lin@gmail.com>, BSD 3-Clause License.
#

"""
The basic/default configuration file for PUG.
"""

__all__ = ['WORKSPACE', 'CODETREE', 'TARGET_TXT']

import os
import sys

sys.dont_write_bytecode = True      # To inhibit the creation of .pyc file

DEFAULT_GCC_TAG = 'GCC5'
DEFAULT_UDK_DIR = os.environ.get('UDK_DIR', os.path.join(os.path.expanduser('~'), '.cache', 'pug', 'edk2'))
DEFAULT_EDK2_TAG = os.environ.get('EDK2_TAG', 'edk2-stable201905')
DEFAULT_MSVC_TAG = os.environ.get('MSVC_TAG', 'VS2012x86')
DEFAULT_EDK2_REPO = os.environ.get('EDK2_REPO', 'https://github.com/tianocore/edk2.git')
DEFAULT_XCODE_TAG = 'XCODE5'
DEFAULT_TARGET_ARCH = os.environ.get('TARGET_ARCH', 'X64')              # 'IA32', 'X64', 'IA32 X64'
DEFAULT_BUILD_TARGET = os.environ.get('BUILD_TARGET', 'RELEASE')        # 'DEBUG', 'NOOPT', 'RELEASE', 'RELEASE DEBUG'
DEFAULT_WORKSPACE_DIR = os.environ.get('WORKSPACE', os.getcwd())
DEFAULT_PATH_APPEND_SIGNATURE = False

CODETREE = {}
PLATFORM = {}
WORKSPACE = {}
COMPONENT = {}
TARGET_TXT = {}

project = None
pCODETREE = {}
pPLATFORM = {}
pWORKSPACE = {}
pCOMPONENT = {}
pTARGET_TXT = {}

ORIGINAL_SYS_PATH = sys.path[:]
try:
    sys.path = [os.getcwd()] + sys.path
    # BUGBUG: Here is a potential vulnerable privilege propagation when importing a local python file.
    import project
    pCODETREE = getattr(project, 'CODETREE', {})
    pPLATFORM = getattr(project, 'PLATFORM', {})
    pWORKSPACE = getattr(project, 'WORKSPACE', {})
    pCOMPONENT = getattr(project, 'COMPONENT', {})
    pTARGET_TXT = getattr(project, 'TARGET_TXT', {})
    for dv in dir(project):
        if not dv.startswith('DEFAULT_'):
            continue
        locals()[dv] = getattr(project, dv)
except ImportError:
    # print('Ingore missing project.py.')
    pass
sys.path = ORIGINAL_SYS_PATH


# Basic global settings of WORKSPACE. Any relative-path is relative to the WORKSPACE-dir.
WORKSPACE = {
    'path'              : DEFAULT_WORKSPACE_DIR,
    'target'            : DEFAULT_BUILD_TARGET,
    'target_arch'       : DEFAULT_TARGET_ARCH,
    'tool_chain_tag'    : DEFAULT_MSVC_TAG if (os.name == 'nt') else DEFAULT_XCODE_TAG if (sys.platform == 'darwin') else DEFAULT_GCC_TAG,
}

WORKSPACE['conf_path'] = os.environ.get('CONF_PATH', os.path.join(WORKSPACE['path'], 'Build', 'Conf'))


# Code tree layout for those remote repository(-ies).
CODETREE = {
    'edk2'              : {
        'source'        : {
            'url'       : DEFAULT_EDK2_REPO,
            'signature' : DEFAULT_EDK2_TAG,
        },
        'recursive'     : True,
        'multiworkspace': True,
    }
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
