#! /usr/bin/env python

import os
import sys
import re
import subprocess

pkgname_regex = re.compile("^(?P<pkgname>[a-z0-9@._+-]+)-(?P<pkgver>[a-z0-9._]+)-(?P<arch>any|x86_64|i686)\.pkg\.tar\.xz(\.sig)?$")

def usage():
    print("Simple utility to clean directories from old pkg.tar.xz files (Arch's packages), keeping only those currently installed")
    print("usage: %s PATH" % sys.argv[0])
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()

    path = sys.argv[1]
    if not os.path.isdir(path):
        usage()
    os.chdir(path)

    # list files in directory
    files = sorted( [f for f in os.listdir() if os.path.isfile(f)] )

    # remove files that don't match pkgname_reges from further processing!!
    for f in files[:]:  # slicing makes copy
        if not re.match(pkgname_regex, f):
            files.remove(f)

    # get list of installed packages
    installed = subprocess.check_output("expac -Qs '%n-%v-%a.pkg.tar.xz'", shell=True, universal_newlines=True).splitlines()

    for f in files:
        # match signature files against pkgname
        if f.endswith(".sig"):
            ff = f[:-4]
        else:
            ff = f

        if ff in installed:
            print("Kept:    %s" % f)
        else:
            print("Deleted: %s" % f)
            os.remove(f)
