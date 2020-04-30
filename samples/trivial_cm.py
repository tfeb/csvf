# A processor module with a trivial context manager

from __future__ import print_function
from sys import stderr

def enter(*args, **options):
    print("entering with {}, options {}".format(args, options),
          file=stderr)

def exit(extype, exval, exb, **options):
    print("exiting with {}, {}, {} & options {}"
          .format(extype, exval, exb, options),
          file=stderr)
    return None

def process(row, **options):
    return row
