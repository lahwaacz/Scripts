#!/usr/bin/env python

# Author: Jakub Klinkovský (Lahwaacz)
# https://github.com/lahwaacz

import sys
import zlib

if len(sys.argv) == 0:
    print("No string specified.")
    sys.exit(1)
elif len(sys.argv) > 2:
    print("Multiple strings specified, specify only one.")
    sys.exit(1)

crc = zlib.crc32(sys.argv[1].encode("utf-8")) & 0xffffffff
crc = str(hex(crc))[2:]
print("52:54:%s%s:%s%s:%s%s:%s%s" % tuple(crc))
