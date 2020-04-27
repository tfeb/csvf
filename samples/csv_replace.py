# A simple CSV-based replacement processor for csvf
#
# This processor reads one or more auxiliary CSV files which should
# contain rows with two elements in.  These files are used to set up a
# table of replacments, which are then applied to the main stream of
# rows.
#

from __future__ import print_function
from csv import reader as csv_reader

class BadRow(Exception):
    # raised if a row in the replacement table is bad
    pass

def validate_row(row, source):
    # Return a row if it's good, else raise an exception.
    # a good row has exactly two elements.
    if len(row) == 2:
        return row
    else:
        raise BadRow("bad row {} from {}".format(row, source))

# A dictionary which will hold the replacements
replacements = {}

def enter(*replacements_files, **junk):
    # called before processing by csvf.  This function expects the
    # names of zero or more replacements files which it will read,
    # check and set up replacements from.
    for replacements_file in replacements_files:
        with open(replacements_file) as input:
            for row in (validate_row(r, replacements_file)
                        for r in csv_reader(input)):
                replacements[row[0]] = row[1]

def process(row):
    # Process a row: simply walk through it and replace anything
    # needed using replacements.  Remember to return the row!
    for (i, e) in enumerate(row):
        if e in replacements:
            row[i] = replacements[row[i]]
    return row
