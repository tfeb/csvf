# csvf
#

"""
``csvf``: cut fields from CSV files
===================================

Usage
-----
::

    csvf [-m mri] [-n] [-D]
         [-d dialect]
         [-c f v] ...
         [-e p r] ...
         [-r s r] ...
         [-P module] ...
         [-A module-arg] ...
         field ... < csvfile

``csvf`` is a filter which prints the fields of a csv file, and can
optionally process them with user-provided code.  Output is csv.

The simplest usage is to select a number of fields::

    csvf 1 2 3 < file.csv

will print the first three fields from ``file.csv``.

Field numbers start from 1: If you give no field specifications all
the fields are printed (but see below).  Field numbers greater than
the length of the row are replaced by the missing record indicator
which is by default ``-``.


Basic options
-------------

``-m  mri``
    sets the missing record indicator, which is by default ``-``.

``-n``
    will suppress all normal output completely.
    Processor modules can still write output.

``-D``
    may help you debug problems: in particular it stops ``csvf`` suppressing
    backtraces on errors, which it does by default.

``-d dialect``
    sets the CSV dialect for both input & output.
    The default is usually fine, but this should be something that
    Python's 'csv' module understands.


Field-editing options
---------------------

``-c f v``
    will force field *f* to value *v*.  ``-c`` is for 'constant'.

``-e f p r``
    will, for field *f*, use *p* and *r* as regexp pattern &
    substitution.  ``-e`` is for 'edit'.

``-r f s r``
    will, if field *f* is the string *s&, replace it by *r*.
    ``-r`` is for 'replace' and this is simpler than using regexps!

The above operations happen in that order: fields are forced to a
constant value, then they are edited as regexps, finally fixed string
replacements happen.  I don't know if this order is best, but that's
what it is.

Field editing operations don't work on missing fields, so you can't
extend rows by forcing fields to a constant.


Options for processor modules
-----------------------------

``-P module``
    names a 'processor module' which is imported.  See below for details
    on these.

``-A arg``
    passes arguments to processor modules.

These options can be repeated for any number of processor modules.
Processing happens before any other operation.

Processor modules
-----------------

A processor module is simply a Python module which is imported in the
normal way.  It should contain at least a function called `process`,
and may also contain functions called `enter` and `exit`.

.. function:: process(row, **kwoptions)

   called to process each row.  `row` is a list, and the function
   should return either another list, or `None`.  If it returns `None`
   then processing for that row stops and nothing is printed.

.. function:: enter(*args, **kwoptions)

   If this function exists, it is called before any processing, with
   any arguments specified by ``-A`` options (if none are specified,
   there will be no arguments).  Its return value is ignored.

.. function:: exit(exc_type, exc_value, exc_traceback, **kwoptions)

   If this function exists it is called after all processing is complete.
   If everything is normal then it will be called with three `None` values.
   If something went wrong it will be called with three values that describe
   the exception that happened.  See the documentation for `with` to
   understand what they are.

For the three functions above, `kwoptions` will include at least
`reader` and `writer` options, whose values will both be functions:

.. function:: reader(stream)

   will return a function which will iterate over the rows of a CSV file
   read from `stream`.

.. function:: writer(stream)

   will return a function which, when called with a row, will write it to
   `stream` as CSV.

Both of these functions respect the dialect option to ``csvf``.

There may in future be other options.


Notes
-----

This is not particularly well-tested code.  Error handling is fairly
rudimentary.

"""

from __future__ import print_function
from sys import stdin, stdout, stderr, argv, exit
from signal import SIGINT
from csv import reader as csv_reader, writer as csv_writer
from argparse import ArgumentParser
from re import compile as re_compile
from importlib import import_module

__all__ = ('main',)

# Default values
default_mri = "-"               # missing record indicator
default_csv_dialect = 'excel'   # default dialect

debugging = False

class PMManager(object):
    """Wraps a processing module to provide a context manager"""
    def __init__(self, processor_module, arguments, **options):
        self.processor_module = processor_module
        self.arguments = arguments
        self.options = options
    def __enter__(self):
        if hasattr(self.processor_module, 'enter'):
            self.processor_module.enter(*self.arguments, **self.options)
    def __exit__(self, extype, exval, extb):
        if hasattr(self.processor_module, 'exit'):
            return self.processor_module.exit(extype, exval, extb,
                                              **self.options)
        else:
            return None
    def process(self, row):
        return self.processor_module.process(row, **self.options)

def main(arguments):
    """The program

    This is given all the commandline arguments except the program
    name.
    """
    global debugging
    parser = ArgumentParser(
        description="cut fields from a CSV file, with possible edits")
    parser.add_argument("-m", "--missing-record-indicator",
                        dest='mri', default=default_mri,
                        help="Printed for missing records, default '{}'"
                        .format(default_mri))
    parser.add_argument("-n", "--no-output",
                        dest='output', action='store_false',
                        help="Suppress output")
    parser.add_argument("-D", "--debugging",
                        dest='debugging', action='store_true',
                        help="debug: don't catch errors, at least")
    parser.add_argument("-c", "--constant",
                        nargs=2, dest='constants', action='append',
                        default=[],
                        metavar=("FIELD", "VALUE"),
                        help="Constant field specifications")
    parser.add_argument("-e", "--edit",
                        nargs=3, dest='edits', action='append',
                        default=[],
                        metavar=("FIELD", "PATTERN", "REPLACEMENT"),
                        help="Edit specifications (regexp replacements)")
    parser.add_argument("-r", "--replacement",
                        nargs=3, dest='replacements', action='append',
                        default=[],
                        metavar=("FIELD", "STRING", "REPLACEMENT"),
                        help="Field replacement specifications")
    parser.add_argument("-d", "--dialect",
                        dest='csv_dialect', default=default_csv_dialect,
                        metavar="DIALECT",
                        help="The CSV dialect, defaultly '{}'"
                        .format(default_csv_dialect))
    parser.add_argument("-P", "--processor-module",
                        dest='processors', action='append',
                        default=[],
                        metavar="MODULE",
                        help="Name of a module to process rows")
    parser.add_argument("-A", "--processor-argument",
                        dest='processor_arguments', action='append',
                        default=[],
                        metavar="ARGUMENT",
                        help="Arguments passed to processor modules")
    parser.add_argument('fields',
                        nargs='*', type=int, default=[],
                        metavar="FIELD",
                        help="The fields to print")
    parsed = parser.parse_args(arguments)
    debugging = parsed.debugging
    mri = parsed.mri
    output = parsed.output
    csv_dialect = parsed.csv_dialect
    if len(parsed.fields) != 0:
        fields = tuple(field -1 for field in parsed.fields)
        for f in fields:
            if f < 0:
                raise Exception("field numbers should be positive")
    else:
        fields = None
    constants = tuple((int(c[0]) -1, c[1])
                      for c in parsed.constants)
    for c in constants:
        if c[0] < 0:
            raise Exception("constant field numbers should be positive")
    edits = tuple((int(e[0]) - 1, re_compile(e[1]), e[2])
                  for e in parsed.edits)
    for e in edits:
        if e[0] < 0:
            raise Exception("edit field numbers should be positive")
    replacements = tuple((int(r[0]) - 1, r[1], r[2])
                         for r in parsed.replacements)
    for r in replacements:
        if r[0] < 0:
            raise Exception("replacement field numbers should be positive")
    reader = (lambda stream:
              csv_reader(stream, dialect=csv_dialect))
    writer = (lambda stream:
              csv_writer(stream, dialect=csv_dialect).writerow)
    processors = tuple(PMManager(import_module(m), parsed.processor_arguments,
                                 reader=reader, writer=writer)
                       for m in ((p[0:-3]
                                  if p.endswith(".py")
                                  else (p[0:-4]
                                        if p.endswith(".pyc")
                                        else p))
                                 for p in parsed.processors))

    def run_with_managers(cm, nm):
        # wrap suitable context managers around execution.  This
        # should be a toplevel function, but it's too fiddly to do
        # now.
        if cm == nm:
            writerow = writer(stdout)
            for row in (rewrite_row(r, processors, constants,
                                    edits, replacements)
                        for r in reader(stdin)):
                if row is None:
                    continue
                l = len(row)
                if output:
                    writerow(tuple((row[f] if f < l else mri)
                                   for f in fields)
                             if fields is not None
                             else row)
        else:
            with processors[cm]:
                run_with_managers(cm + 1, nm)

    run_with_managers(0, len(processors))
        
def rewrite_row(row, processors, constants, edits, replacements):
    """Destructively rewrite the fields in a row

    This rewrites `row` according to `processors`, `replacements`,
    `edits` & `constants` Note the order this happens: rows are
    processed by all of the processors, then fields are first driven
    to constants, then edits are done, then fixed replacements are
    done.  I am not sure if this is the best order, but it seems
    reasonable.  This can mutate row.
    """
    l = len(row)
    for p in processors:
        row = p.process(row)
        if row is None:
            return None
    for (f, c) in constants:
        if f < len(row):
            row[f] = c
    for (f, p, r) in edits:
        if f < len(row):
            row[f] = p.sub(r, row[f])
    for (f, s, r) in replacements:
        if f < len(row):
            if row[f] == s:
                row[f] = r
    return row


if __name__ == '__main__':
    try:
        main(argv[1::])
    except Exception as e:
        if not debugging:
            exit(e)
        else:
            raise
    except KeyboardInterrupt as e:
        exit(128 + SIGINT)
