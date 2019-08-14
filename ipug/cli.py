# -*- coding: utf-8 -*-

"""Console script for ipug."""
import os
import sys
# import time
# import click

try:
    from ipug.ipug import main as ipug_main
    from ipug.__init__ import __version__
except ImportError:
    from ipug import main as ipug_main
    from __init__ import __version__


# @click.command()
def main():
    """main"""
    sysargv = sys.argv[1:]
    if '--version' in sysargv:
        print('PUG version: {}'.format(__version__))
        return 0
    if '--help' in sysargv:
        print('Usage: {--version|--help|--dump-default-config}')
        return 0
    if '--dump-default-config' in sysargv:
        cfg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.py')
        try:
            with open(cfg_path, 'r') as fin:
                content = fin.read()
                print('The default config file: {}'.format(cfg_path))
                print('{}'.format(content))
        except Exception:
            print('--empty--')
        return 0
    return ipug_main()

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
