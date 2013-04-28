#!/usr/bin/env python

import sys
import os


def rename(old, new):
    stat = os.stat(old)
    os.rename(old, new)
    os.utime(new, (stat.st_atime, stat.st_mtime))

if os.path.isfile(sys.argv[1]):
    basenameOld = os.path.splitext(sys.argv[1])[0]
    basenameNew = os.path.splitext(sys.argv[2])[0]

    for ext in [".avi", ".mkv", ".mp4", ".m4v", ".en.srt", ".eng.srt", ".eng.sub", ".cs.srt", ".cze.srt", ".cze.sub"]:
        if os.path.isfile(basenameOld + ext):
            print(basenameOld + ext + "  =>  " + basenameNew + ext)
            rename(basenameOld + ext, basenameNew + ext)
