# The antifish processor module
#
# Put this somwhere in PYTHONPATH (the current directory is fine) and
# run csvf -p antifish ...
#

def process(row):
    if len(row) >= 1 and row[0] == "fish":
        return None
    else:
        return row
