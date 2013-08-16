#! /usr/bin/env python

import os
import sys
import shutil

images = os.listdir(".")
images = [x for x in images if x.endswith(".tiff")]
images.sort()

for image in images:
    i = images.index(image) + 1
    new = "page_%03d.tiff" % i
    print("mv '%s' '%s'" % (image, new))
    shutil.move(image, new)
