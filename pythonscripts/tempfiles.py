#! /usr/bin/env python

"""
Create temporary file, close file descriptor and return full path of the file.
"""

import os
import tempfile
import atexit

class TempFiles:
    def __init__(self):
        self.tempFiles = []
        atexit.register(self.removeAll)

    def removeAll(self):
        for file in self.tempFiles[:]:
            self.remove(file)

    def remove(self, file):
        if file in self.tempFiles and os.path.exists(file):
            os.remove(file)
            self.tempFiles.remove(file)

    def getTempFileName(self, prefix="tmp", suffix="", dir=None, text=False):
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir, text=text)
        os.close(fd)
        self.tempFiles.append(path)
        return path

