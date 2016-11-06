#! /usr/bin/env python

import os
import sys
import re
import subprocess

pkgname_regex = re.compile("^(?P<pkgname>[a-z0-9@._+-]+)-(?P<pkgver>[a-z0-9._:-]+)-(?P<arch>any|x86_64|i686)\.pkg\.tar(\.xz)?(\.sig)?$", re.IGNORECASE)

def usage():
    print("Simple utility to clean directories from old Arch's package files, keeping only those currently installed")
    print("usage: %s PATH" % sys.argv[0])
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()

    path = sys.argv[1]
    if not os.path.isdir(path):
        usage()
    os.chdir(path)

    files = {}

    # remove files that don't match pkgname_reges from further processing!!
    for f in os.listdir():
        if not os.path.isfile(f):
            continue
        match = re.match(pkgname_regex, f)
        if match:
            # strip extension for future comparison with expac's output
            files[f] = "{pkgname}-{pkgver}-{arch}".format(**match.groupdict())

    # get list of installed packages
    installed = subprocess.check_output("expac -Qs '%n-%v-%a'", shell=True, universal_newlines=True).splitlines()

    for f in sorted(files):
        # compare with the key instead of the whole filename
        # (drops file extensions like .pkg.tar.{xz,gz}{,.sig} )
        ff = files[f]

        if ff in installed:
            print("Kept:    %s" % f)
        else:
            print("Deleted: %s" % f)
            os.remove(f)
