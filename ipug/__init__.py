"""
PUG: 'Pug, the UDK Guidedog', or 'the Programmer's UDK Guide'.
A front-end to build the UDK driver(s) with only .C source files and a .PY as the config file.

(c) 2019-2020 Timothy Lin <timothy.gh.lin@gmail.com>, BSD 3-Clause License."""

from .ipug import main

__author__ = 'Timothy Lin (timothy.gh.lin@gmail.com)'
__version__ = '0.2.3'

main = main

if __name__ == '__main__':
    print('Bow-wow!')
