#! /usr/bin/env python

import os
import sys
import shutil


shittyfiles = [
    '~/.adobe',              # Flash crap
    '~/.macromedia',         # Flash crap
    '~/.recently-used',
    '~/.local/share/recently-used.xbel',
    '~/Desktop',             # Firefox creates this
    '~/.thumbnails',
    '~/.gconfd',
    '~/.gconf',
    '~/.local/share/gegl-0.2',
    '~/.FRD/log/app.log',   # FRD
    '~/.FRD/links.txt',     # FRD
    '~/.objectdb',          # FRD
    '~/.gstreamer-0.10',
    '~/.pulse',
    '~/.esd_auth',
    '~/.config/enchant',
    '~/.spicec',            # contains only log file; unconfigurable
    '~/.dropbox-dist',
    '~/.parallel',
    '~/.dbus',
    '~/ca2',                # WTF?
    '~/ca2~',               # WTF?
    '~/.distlib/',          # contains another empty dir, don't know which software creates it
    '~/.bazaar/',           # bzr insists on creating files holding default values
    '~/.bzr.log',
    '~/.nv/',
    '~/.viminfo',           # configured to be moved to ~/.cache/vim/viminfo, but it is still sometimes created...
    '~/.npm/',              # npm cache
    '~/.java/',
    '~/.oracle_jre_usage/',
    '~/.jssc/',
    '~/.tox/',              # cache directory for tox
    '~/.pylint.d/',
]


def yesno(question, default="n"):
    """ Asks the user for YES or NO, always case insensitive.
        Returns True for YES and False for NO.
    """
    prompt = "%s (y/[n]) " % question

    ans = input(prompt).strip().lower()

    if not ans:
        ans = default

    if ans == "y":
        return True
    return False


def rmshit():
    print("Found shittyfiles:")
    found = []
    for f in shittyfiles:
        absf = os.path.expanduser(f)
        if os.path.exists(absf):
            found.append(absf)
            print("    %s" % f)

    if len(found) == 0:
        print("No shitty files found :)")
        return

    if yesno("Remove all?", default="n"):
        for f in found:
            if os.path.isfile(f):
                os.remove(f)
            else:
                shutil.rmtree(f)
        print("All cleaned")
    else:
        print("No file removed")


if __name__ == '__main__':
    rmshit()
