#! /usr/bin/env python

import os
import subprocess
import re
import fnmatch
import hashlib
import shutil

repo_path = "~/GitHub-repos/archlinux-dotfiles"

# str src: absolute path!
# str git: relative to 'repo_path'
# bool only-update: True will update only files existing in 'git', False will copy all files from 'src' to 'git'
# str: find-params: custom arguments for find (added to 'find <target>' command), useful to filter files
mappings = [
    {"src": "~/",               "git": "./home",    "only-update": True,    "find-params": "-type f -print"}, 
    {"src": "/etc",             "git": "./etc",     "only-update": True,    "find-params": "-type f -print"}, 
    {"src": "/usr",             "git": "./usr",     "only-update": True,    "find-params": "-type f -print"}, 
    {"src": "~/Scripts",        "git": "./Scripts", "only-update": False,   "find-params": "-type f -print"}, 
    {"src": "~/aur/build-dirs", "git": "./Build",   "only-update": False,   "find-params": "-mindepth 2 -maxdepth 2 -name \"PKGBUILD\" -type f -print0 | xargs -0 grep -l \"groups=('modified')\""}, 
]

# blacklist - never copy
blacklist = [
    "/etc/grub.d/01_password-security",
    "~/Scripts/backup-wordpress-kmlinux-server-side.sh",
]

# whitelist - always copy (override blaclist)
whitelist = []

""" Remap 'src' to 'dest' in path
"""
def remap(path, src, dest):
#    return str(path).replace(src, dest, 1)
    if path.startswith(src):
        return dest + path[len(src):]
    return path

""" Calculate file hash, return hexdigest
"""
def fhash(path):
    if os.path.isfile(path):
        f = open(path, 'rb')
        h = hashlib.new('sha256')
        h.update(f.read())
        f.close()
        return h.hexdigest()
    return None

class Sync(object):
    def __init__(self, mappings, whitelist, blacklist):
        self.mappings = mappings
        self.whitelist = whitelist
        self.blacklist = blacklist

        self.files = []     # list of (<src>, <dest>) tuples for each file that is to be transferred

    def run(self):
        del self.files[:]   # clear list in case of repeated use
        self.find()
        self.filter_blacklisted()
        self.filter_updated()
        self.copy()

    def find(self):
        for mapping in self.mappings:
            # convert to absolute path
            mapping["src"] = os.path.abspath(os.path.expanduser(mapping["src"]))

            if mapping["only-update"]:
                # <src>, <dest> is swapped
                cmd = "find %s  %s" % ( mapping["git"], mapping["find-params"] )
                dest_files = subprocess.check_output(cmd, shell=True, universal_newlines=True).splitlines()
                src_files = [remap(f, mapping["git"], mapping["src"]) for f in dest_files]
            else:
                # normal behavior
                cmd = "find %s  %s" % ( mapping["src"], mapping["find-params"] )
                src_files = subprocess.check_output(cmd, shell=True, universal_newlines=True).splitlines()
                dest_files = [remap(f, mapping["src"], mapping["git"]) for f in src_files]

            self.files.extend(list(zip(src_files, dest_files)))

            if mapping["only-update"]:
                # filter non-existent files, display warning
                for item in self.files[:]:  # slicing makes copy
                    fname = item[0]
                    if not os.path.exists(fname):
                        print("WARNING: file doesn't exist: %s" % fname)
                        self.files.remove(item)

    def filter_blacklisted(self):
        def matches(reobjects, fname):
            for reobj in reobjects:
                if reobj.match(fname):
                    return True
            return False

        for item in self.files[:]:  # slicing makes copy
            fname = item[0]

            # don't remove if in whitelist
            if matches(whitelist, fname):
                print("Whitelisted %s" % fname)
                continue

            if matches(blacklist, fname):
                print("Blacklisted %s" % fname)
                self.files.remove(item)

    def filter_updated(self):
        for item in self.files[:]:  # slicing makes copy
            src = item[0]
            dest = item[1]

            # leave if dest doesn't exist (we can't calculate hash)
            if not os.path.exists(dest):
                continue
            
            if fhash(src) == fhash(dest) and os.path.getmtime(src) <= os.path.getmtime(dest):
                self.files.remove(item)

    def copy(self):
        for item in self.files:
            src = item[0]
            dest = item[1]

            print("Copying %s\n    to %s" % (src, dest))
            shutil.copy2(src, dest)



if __name__ == "__main__":
    # change to repo dir
    os.chdir(os.path.expanduser(repo_path))

    # translate white/black lists into regex objects
    whitelist = [re.compile(fnmatch.translate(os.path.expanduser(pattern))) for pattern in whitelist]
    blacklist = [re.compile(fnmatch.translate(os.path.expanduser(pattern))) for pattern in blacklist]

    sync = Sync(mappings, whitelist, blacklist)
    sync.run()
