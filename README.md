# `csvf`
The CSV Filter is a simple field extractor for CSV files, written in Python 2 (as it's quite old).

Until recently this existed only as a gist, but since it's going to be souped up somewhat it is now a proper repo.

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

The input format is always CSV: you can control the dialect with the `-d` option below.  `csvf`'s understanding of CSV should be as good as that of the Python `csv` module which it uses.

But unless you use `-w` (below) the output is *not* CSV!  Instead the output format is controlled by three options, and there is no fancy escaping of commas and quotes.

- `-s sep` controls the separator between fields, which is defaultly a space character.
- `-m mri` controls what is printed for a missing field – usually if you've tried to print a field beyond the end of the row.  By default it is `-`.
- `-f fmt` controls how each field is printed.  This is a Python format string.  By default it is `"{0}"` which means there are double quotes around each field: you can change this by, for instance `csvf -f '{0}' ...` which will not print any quotes at all.

But if you use `-w` then the output *is* CSV.

- `-w` causes it to write CSV using Python's support for that.  In that case only the missing record indicator matters: everything else is dealt with by the CSV writer.
- `-d dialect` sets the CSV dialect for both input & output.  See the Python `csv` module documentation for which dialects exist, but the default is usually fine.

In addition you can *edit* the output in various ways.

- `-c f v` will force field `f` to be the string `v`.
- `-e f p r` will, for field `f`, do a regular expression replacement of `p` by `r`.  This is the hairiest editing option.
- `-s f s r` will, for field `f`, replace it by `r` if it is the string `s`.  This is a simpler editing option.

All of these options can be specified as many times as you like.  The operations take place in that order: fields are set to constants, then regular expressions are replaced, then fixed strings are replaced.  There is only one pass, so you can't do clever trickery like replacing regular expressions with patterns that other regular expressions will match.  The operations only work on non-missing fields: you can't extend rows by forcing fields to be a constant.

## Examples
Given this CSV file, `foo.csv`:

```
fish,bat,bone
fish,dog,spot
bird,cake,hoover
```

Then

```
$ csvf <foo.csv
"fish" "bat" "bone"
"fish" "dog" "spot"
"bird" "cake" "hoover"
$ csvf -s: -f '{0}' <foo.csv
fish:bat:bone
fish:dog:spot
bird:cake:hoover
$ csvf -s: -f '{0}' -r 1 fish bat <foo.csv
bat:bat:bone
bat:dog:spot
bird:cake:hoover
$ csvf -s: -f '{0}' -e 2 '^ba' bi <foo.csv
fish:bit:bone
fish:dog:spot
bird:cake:hoover
$ csvf -w 1 2 <foo.csv
fish,bat
fish,dog
bird,cake
```

## Processor modules
`csvf` has one more feature: you can specify Python code that you write which gets to process rows.  This is done by the `-p module` option, which will cause `csvf` to dynamically import `module` when it runs. `-p` options can many times and all of the specified modules will be loaded.

A processor module should contain a function called `process`: this function has one argument, the row (which will be a list or tuple) and should return either a row, or `None`.  If it returns a row, then that is used by later stages of the program, including any later processor modules.  If it returns `None` no further processing is done and the row is not printed.

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
$ ./csvf -w  < samples/foo.csv
fish,bat,bone
fish,dog,spot
bird,cake,hoover
$ ./csvf -w  -p antifish < samples/foo.csv
bird,cake,hoover
```

As you can see, the rows whose first element is `"fish"` have been suppressed.

Processor modules mean that you can perform completely arbitrary computations on and transformations of a row.

## Notes
`csvf` makes no attempt to deal with fields that contain the output field separator or the no-field indicator.  If you want to extract fields which contain these the separator, then the way to do it is to extract them one at a time, so you know there is one field per line.  I don't think there's any way at all to detect missing fields reliably as it stands.

This is not particularly well-tested code.  Error handling is rudimentary.

It should work in Python 2.7.  If you want it to work on 2.6 let me know (but it may be hard to backport now).

In the future there may be a version which is much closer to a simple library for processing CSV files: it should be possible to specify filenames on the command line, and it should be possible to process many files.  However there are already existing programs which provide functionality like this, and making `csvf` too complicated would result in a not-as-good version of those systems rather than a small, simple tool: so that future version may never exist.
