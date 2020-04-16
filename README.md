# `csvf`
This is a simple field extractor for CSV files, written in Python 2 (as it's quite old).

Until recently this existed only as a gist, but since it's going to be souped up somewhat it is now a proper repo.

## Notes
It makes no attempt to deal with fields that contain the output field separator `sep`, or the no-field indicator `oor`.  If you want to extract fields which contain `sep`, then the way to do it is to extract them one at a time, so you know there is one field per line.  I don't think there's any way at all to detect missing fields reliably as it stands.

It should work in Python 2.7.  If you want it to work on 2.6 let me know.
