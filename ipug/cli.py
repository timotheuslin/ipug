# -*- coding: utf-8 -*-

"""Console script for ipug."""
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
    if '--version' in sys.argv[1:]:
        print('PUG version: {}'.format(__version__))
        return 0
    return ipug_main()


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
