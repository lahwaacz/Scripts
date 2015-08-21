#! /usr/bin/env python

"""
Simple logger object. Log level is integer for easy comparison.
"""

import sys

class Logger:
   def __init__(self, log_level, prog_name):
       self.log_level = log_level
       self.prog_name = prog_name
       self.filename = None

   def prefix(self, msg):
       if self.filename is None:
           return msg
       return "%s: %s" % (self.filename, msg)

   def debug(self, msg):
       if self.log_level >= 4:
           print(self.prefix(msg))

   def info(self, msg):
       if self.log_level >= 3:
           print(self.prefix(msg))

   def warning(self, msg):
       if self.log_level >= 2:
           print(self.prefix("WARNING: %s" % msg))

   def error(self, msg):
       if self.log_level >= 1:
           sys.stderr.write("%s: %s\n" % (self.prog_name, msg))

   def critical(self, msg, retval=1):
       self.error(msg)
       sys.exit(retval)
