#! /usr/bin/env python

"""
Linux terminal colors.
"""

#import sys

COLORS = {"black":30, "red":31, "green":32, "yellow":33, "blue":34, "magenta":35, "cyan":36, "white":37}

def colorize(color, text):
    c = COLORS[color]
    return "\033[1;%im%s\033[0m" % (c, text)
#    if sys.stdout.isatty():
#        c = COLORS[color]
#        return "\033[1;%im%s\033[0m" % (c, text)
#    else:
#        return text

def getColor(status, download_speed=0):
    if status == "error":
        return "red"
    elif status == "active":
        if download_speed > 0:
            return "blue"
        else:
            return "yellow"
    elif status == "complete":
        return "green"
    elif status == "paused":
        return "cyan"
    elif status == "waiting":
        return "magenta"
    else:
        return ""



"""
Get size of unix terminal as tuple (width, height).
When all fails, default value is (80, 25).

Original source code from:
http://stackoverflow.com/a/566752
"""

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])

