#! /usr/bin/env python

"""
Get status and output of any command, capable of handling unicode.
"""

import subprocess
import codecs

from tempfiles import *

tmp = TempFiles()

def getstatusoutput(cmd):
    logname = tmp.getTempFileName()
    log = codecs.open(logname, mode="w", encoding="utf-8", errors="replace", buffering=0)
    popen = subprocess.Popen(cmd, shell=True, stdout=log, stderr=subprocess.STDOUT, universal_newlines=True)
    status = popen.wait()
    log.close()
    log = codecs.open(logname, mode="r", encoding="utf-8", errors="replace")
    output = log.read()
    log.close()
    tmp.remove(logname)
    return status, output

def getstatus(cmd):
    return getstatusoutput(cmd)[0]

def getoutput(cmd):
    return getstatusoutput(cmd)[1]

