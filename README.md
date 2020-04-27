# `csvf`
The CSV Filter is a simple field extractor for CSV files, written in Python 2 (as it's quite old).

Until recently this existed only as a gist, but since it's now been souped up somewhat it is now a proper repo.

## What it can do
It works as a filter, so you want to use it as

```
$ csvf ... < file.csv
```

The simplest usage is just to give it a bunch of field numbers, with the first field being `1`.  So


```
$ csvf 1 3 < file.csv
```

will print the first and third field from `file.csv`.  If you give it no field numbers it will print the entire row.

The input and output format is CSV.  `csvf`'s understanding of CSV should be as good as that of the Python `csv` module which it uses.

## Basic options

- `-m mri` controls what is printed for a missing field – usually if you've tried to print a field beyond the end of the row.  By default it is `-`.
- `-n` will suppress all normal output completely.  Processor modules can still write output.
- `-D` may help you debug problems: in particular it stops `csvf` suppressing backtraces on errors, which it does by default.

- `-d dialect` sets the CSV dialect for both input & output.
    The default is usually fine, but this should be something that Python's 'csv' module understands.

## Field-editing options
You can *edit* the output in various ways.

- `-c f v` will force field `f` to be the string `v`.
- `-e f p r` will, for field `f`, do a regular expression replacement of `p` by `r`.  This is the hairiest editing option.
- `-s f s r` will, for field `f`, replace it by `r` if it is the string `s`.  This is a simpler editing option.

All of these options can be specified as many times as you like.  The operations take place in that order: fields are set to constants, then regular expressions are replaced, then fixed strings are replaced.  There is only one pass, so you can't do clever trickery like replacing regular expressions with patterns that other regular expressions will match.  The operations only work on non-missing fields: you can't extend rows by forcing fields to be a constant.

## Examples
Given this CSV file, `samples/foo.csv`:

```
fish,bat,bone
fish,dog,spot
bird,cake,hoover
```

Then

```
$ csvf < samples/foo.csv
fish,bat,bone
fish,dog,spot
bird,cake,hoover
$ csvf 1 2 < samples/foo.csv
fish,bat
fish,dog
bird,cake
$ csvf -c 2 bat 1 2 < samples/foo.csv
fish,bat
fish,bat
bird,bat
$ csvf -r 1 bird fish < samples/foo.csv
fish,bat,bone
fish,dog,spot
fish,cake,hoover
$ csvf -e 1 i u -e 2 '^.' 'c' 1 2 < samples/foo.csv
fush,cat
fush,cog
burd,cake
```

## Processor modules
`csvf` has one more feature: you can specify Python code that you write which gets to process rows.  This is done by the `-P module` option, which will cause `csvf` to dynamically import `module` when it runs. `-P` options can many times and all of the specified modules will be loaded.  `-A arg` options can be used to provide arguments to processor modules (see below).

A processor module should contain a function called `process`: this function has one argument, the row (which will be a list or tuple) and should return either a row, or `None`.  If it returns a row, then that is used by later stages of the program, including any later processor modules.  If it returns `None` no further processing is done and the row is not printed.  Processing happens before any of the above processes.

Additionally, processor modules can wrap their own code around the whole process.  This is done by Python's 'context manager' mechanism.  If a processor module contains a function called `enter`, this function will be called, with any arguments provided by `-A` options, before any work is done.  If it contains a function called `exit`, this will be called with three arguments after all processing is complete.  The three arguments it is called with will normally all be `None` but if any exception is raised they will be the type of the exception, its value, and a traceback object.  Apart from the extra arguments passed to the `enter` function, both of these functions are semantically simply the `__enter__` and `__exit__` functions of a context manager: see the Python documentation for the details of this.

Processor modules are imported in the usual way Python imports modules using `import`: this means that they can live anywhere on `PYTHONPATH`, but in practice the easiest thing is to simply have a Python (`.py`) file in the current directory.  One thing you *can't* do is to import modules by pathname, because that's slightly hard to do.  One side-effect of importing a module is that the Python file it corresponds to will get compiled, so for a processor module `foo.py` you will find `foo.pyc` after running `csvf -p foo ...`: those compiled files can be safely removed.

Here is an example processor module, called `antifish.py`:

```
def process(row):
    if len(row) >= 1 and row[0] == "fish":
        return None
    else:
        return row
```

What this does is: check that the row has at least one element, and if it does check whether the first element is the string `"fish"`.  If it is, it rejects the row, otherwise it returns it.  Here is this in action:

```
$ csvf < samples/foo.csv
fish,bat,bone
fish,dog,spot
bird,cake,hoover
$ ./csvf -P antifish < samples/foo.csv
bird,cake,hoover
```

As you can see, the rows whose first element is `"fish"` have been suppressed.

Here is a simple module called `trivial_cm.py`, which demonstrates the context manager features:

```
from __future__ import print_function
from sys import stderr

def enter(*args):
    print("entering with {}".format(args), file=stderr)

def exit(*vals):
    print("exiting with {}".format(vals), file=stderr)
    return None

def process(row):
    return row
```

Here this is in action:

```
$ csvf -P trivial_cm -A arg -A another < samples/foo.csv >/dev/null
entering with ('arg', 'another')
exiting with (None, None, None)
```

Processor modules mean that you can perform completely arbitrary computations on and transformations of a row.

`samples/csv_replace.py` is an example processor module which will use auxilliary CSV files to drive replacements.

## Notes
Samples and examples, including example processor modules, can be found in `samples/`.

`csvf` makes no attempt to deal with fields missing record indicator.

This is not particularly well-tested code.  Error handling is fairly rudimentary.

It should work in Python 2.7.  If you want it to work on 2.6 let me know (but it may be hard to backport now).  It should be very easy to port to Python 3, simply using `2to3`.

In the future there may be a version which is much closer to a simple library for processing CSV files: it should be possible to specify filenames on the command line, and it should be possible to process many files.  However there are already existing programs which provide functionality like this, and making `csvf` too complicated would result in a not-as-good version of those systems rather than a small, simple tool: so that future version may never exist.
