# -*- coding: utf-8 -*-

"""Console script for ipug."""
import sys
import time
import click

try:
    from ipug.ipug import main as ipug_main
except ImportError:
    from ipug import main as ipug_main


#@click.command()
def main():
    """main"""
    return ipug_main()

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
