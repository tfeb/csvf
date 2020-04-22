# A processor module with a trivial context manager

from __future__ import print_function
from sys import stderr

def enter(*args):
    print("entering with {}".format(args), file=stderr)

def exit(*vals):
    print("exiting with {}".format(vals), file=stderr)
    return None

def process(row):
    return row
