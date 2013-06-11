#! /usr/bin/env python

"""
Human-readable file size. Algorithm does not use a for-loop. It has constant
complexity, O(1), and is in theory more efficient than algorithms using a for-loop.

Original source code from:
http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
"""

from math import log

unit_list = {
    "long": list(zip(['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'], [0, 0, 1, 2, 2, 2])),
    "short": list(zip(['B', 'K', 'M', 'G', 'T', 'P'], [0, 0, 1, 2, 2, 2])),
}

def format_sizeof(num, unit_format="long"):
    if num > 1:
        exponent = min(int(log(num, 1024)), len(unit_list[unit_format]) - 1)
        quotient = float(num) / 1024**exponent
        unit, num_decimals = unit_list[unit_format][exponent]
        format_string = '{:.%sf} {}' % (num_decimals)
        return format_string.format(quotient, unit)
    else:
        return str(int(num)) + " B"



"""
Nice time format, useful for ETA etc. Output is never longer than 6 characters.
"""

def format_time(seconds):
    w, s = divmod(seconds, 3600*24*7)
    d, s = divmod(s, 3600*24)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if w > 0:
        return "%dw" % w
    if d > 0:
        return "%dd%02dh" % (d, h)
    if h > 0:
        return "%02dh%02dm" % (h, m)
    if m > 0:
        return "%02dm%02ds" % (m, s)
    return str(s)



"""
Get content of any readable text file.
"""

def cat(fname):
    try:
        f = open(fname, "r")
        s = f.read()
        f.close()
        return s.strip()
    except:
        return None



"""
Returns a string of at most `max_length` characters, cutting
only at word-boundaries. If the string was truncated, `suffix`
will be appended.
"""

import re

def smart_truncate(text, max_length=100, suffix='...'):
    if len(text) > max_length:
        pattern = r'^(.{0,%d}\S)\s.*' % (max_length-len(suffix)-1)
        return re.sub(pattern, r'\1' + suffix, text)
    else:
        return text



"""
Recursive directory creation function (like 'mkdir -p' in linux).
"""

import os

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != 17:
            raise e
