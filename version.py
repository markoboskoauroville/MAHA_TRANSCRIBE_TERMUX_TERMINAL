"""
version.py  --  the single number everything else reads.

One whole number per modules/versioning.md: v1, v2, v3, never a dot.
Every change, however small, is a new number. Bumped by hand on every
commit that touches this app's server side (app.py, console.py,
localguard.py, portpick.py, audioprep.py, selfupdate.py).

Kept in its own file rather than inside app.py so selfupdate.py can read
it without importing app.py itself -- app.py imports selfupdate.py, and a
module that imports the thing that imports it is a circular import.
"""

APP_VERSION = 4
