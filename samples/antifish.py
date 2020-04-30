# The antifish processor module
#
# Put this somwhere in PYTHONPATH (the current directory is fine) and
# run csvf -P antifish ...
#

def process(row, **options):
    if len(row) >= 1 and row[0] == "fish":
        return None
    else:
        return row
