# `csvf`
The CSV Filter is a simple field extractor for CSV files, written in Python 2 (as it's quite old).

Until recently this existed only as a gist, but since it's now been souped up somewhat it is now a proper repo.

## What is here
The program you run is `bin/csvf`: it's a tiny shell script which expects to find `lib/csvf.py` in the right place, so if you copy one, copy the other, and preserve the directory structure: `bin/../lib/csvf.py` should be the right file.

**Important note.** If the `PYTHONPATH` environment module is not set, then `bin/csvf` will set it to `.`, which means that processor modules will be looked for in the directory from which the script is invoked, as well as next to `lib/csvf.py` and along the default search path.  This is usually what you want, but does mean that you could subvert standard modules by putting bogus copies in the current directory.  If `PYTHONPATH` *is* set, it won't prepend or append `.` however.

As well as the `bin` and `lib` directories:

- `samples/` contains some samples, both of Python code and CSV files.
- `doc/` contains the probably-abandoned beginnings of a [Sphinx](https://www.sphinx-doc.org/)-based documentation generator.  There is no actual documentation there currently, but if you have sphinx you could perhaps try to make some.

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
`csvf` has one more feature: you can specify Python code that you write which gets to process rows.  This is done by the `-P module` option, which will cause `csvf` to dynamically import `module` when it runs.  Any `.py` or `.pyc` suffix is stripped from `module`'s name, so it works to say `-P foo.py` if `foo.py` is in the current directory: this helps with shell completion.  `-P` options can be repeated many times and all of the specified modules will be loaded.  `-A arg` options can be used to provide arguments to processor modules (see below).

A processor module should contain a function called `process`: this function has one positional argument and some keyword arguments.  The positional argument is the row (which will be a list or tuple), for the keyword arguments see below.  The function should return either a row, or `None`: if it returns a row, then that is used by later stages of the program, including any later processor modules.  If it returns `None` no further processing is done and the row is not printed.  Processing happens before any of the built-in editing processes.

Additionally, processor modules can wrap their own code around the whole process.  This is done by Python's 'context manager' mechanism.  If a processor module contains a function called `enter` then this function will be called, with any arguments provided by `-A` options, as well as some keyword arguments (see below), before any work is done.

If a processor module contains a function called `exit`, this will be called with three arguments and some keyword arguments (see below) after all processing is complete.  The three arguments it is called with will normally all be `None` but if any exception is raised they will be the type of the exception, its value, and a traceback object.

Apart from the extra arguments passed, the `enter` and `exit` functions are semantically simply the `__enter__` and `__exit__` functions of a context manager: see the Python documentation for the details of this.

The keyword arguments passed to the above functions are all the same, and will include at least:

- `reader`, which is a function which, when called with a stream, will return a function which will iterate over the CSV file read from that stream;
- `writer`, which is a function which, when called with a stream, will return a function which, when called with a row, will write that row to the stream as CSV.

Both of these functions respect the selected CSV dialect, and they mean that processor modules can read & generate CSV without needing to talk to the `csv` module themselves.

Processor modules are imported in the usual way Python imports modules using `import`: this means that they can live anywhere on `PYTHONPATH`, but in practice the easiest thing is to simply have a Python (`.py`) file in the current directory.  One thing you *can't* do is to import modules by pathname, because that's slightly hard to do.  One side-effect of importing a module is that the Python file it corresponds to will get compiled, so for a processor module `foo.py` you will find `foo.pyc` after running `csvf -P foo ...`: those compiled files can be safely removed.

Here is an example processor module, called `antifish.py`:

```
def process(row, **options):
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

def enter(*args, **options):
    print("entering with {}, options {}".format(args, options),
          file=stderr)

def exit(extype, exval, exb, **options):
    print("exiting with {}, {}, {} & options {}"
          .format(extype, exval, exb, options),
          file=stderr
    return None

def process(row, **options):
    return row
```

Here this is in action:

```
$ csvf -D -P trivial_cm < samples/foo.csv
entering with (), options {'writer': <function <lambda> at 0x10be9faa0>, 'reader': <function <lambda> at 0x10be9f8c0>}
fish,bat,bone
fish,dog,spot
bird,cake,hoover
exiting with None, None, None & options {'writer': <function <lambda> at 0x10be9faa0>, 'reader': <function <lambda> at 0x10be9f8c0>}
```

Processor modules mean that you can perform completely arbitrary computations on and transformations of a row.

`samples/csv_replace.py` is an example processor module which will use auxilliary CSV files to drive replacements.

## Notes
`csvf` makes no attempt to deal with fields which are the same as the missing record indicator.

This is not particularly well-tested code.  Error handling is fairly rudimentary.

It should work in Python 2.7.  If you want it to work on 2.6 let me know (but it may be hard to backport now).  It should be very easy to port to Python 3, simply using `2to3`.

In the future there may be a version which is much closer to a simple library for processing CSV files: it should be possible to specify filenames on the command line, and it should be possible to process many files.  However there are already existing programs which provide functionality like this, and making `csvf` too complicated would result in a not-as-good version of those systems rather than a small, simple tool: so that future version may never exist.
