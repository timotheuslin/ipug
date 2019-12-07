"""
PUG: 'Pug, the UDK Guidedog', or 'the Programmer's UDK Guide'.
A front-end to build the UDK driver(s) with only .C source files and a .PY as the config file.

(c) 2019 Timothy Lin <timothy.gh.lin@gmail.com>, BSD 3-Clause License."""

import sys
from .ipug import main

sys.exit(main())
