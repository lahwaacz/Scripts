#! /usr/bin/env python

import os
import subprocess
import re
import fnmatch
import hashlib
import shutil

# path to git root directory
repo_path = "~/GitHub-repos/archlinux-dotfiles"

## 'mappings' is list of dicts containing these keys:
# str src:  absolute path (expansion of '~' is supported)
# str git:  relative to 'repo_path'
## optional:
# bool only-update:     If True, only files existing in 'git' will be copied. If False, all files from 'src' will be copied to 'git'. Defaults to True.
# bool delete-before:   If True, all files present in 'git' are deleted before copying. This avoids leaving files not present in 'src'. Defaults to False.
# str find-params:      Custom arguments for find (added to 'find <target>' command), useful to filter files. Defaults to "-type f -print".
mappings = [
    {
        "src": "~/",
        "git": "./home",
        "find-params": "-type f ! -wholename \"./home/.config/systemd/*\"",
    }, 
    {
        "src": "/etc",
        "git": "./etc",
        "find-params": "-type f ! -wholename \"./etc/systemd/*\"",
    }, 
    {
        "src": "/usr",
        "git": "./usr",
    }, 
    {
        "src": "~/Scripts",
        "git": "./Scripts",
        "only-update": False,
    }, 
    {
        "src": "~/aur/build-dirs",
        "git": "./Build",
        "only-update": False,
        "find-params": "-mindepth 2 -maxdepth 2 -name \"PKGBUILD\" -type f -print0 | xargs -0 grep -l \"groups=('modified')\"",
    }, 

    # copy systemd separately, delete files missing in 'src', make full copy
    {
        "src": "~/.config/systemd",
        "git": "./home/.config/systemd",
        "delete-before": True,
        "only-update": False,
        "find-params": "! -type d",
    },
    {
        "src": "/etc/systemd",
        "git": "./etc/systemd",
        "delete-before": True,
        "only-update": False,
        "find-params": "! -type d",
    },
]

# blacklist - never copy
blacklist = [
    "/etc/grub.d/01_password-security",
    "~/Scripts/backup-wordpress-kmlinux-server-side.sh",
]

# whitelist - always copy (override blaclist)
whitelist = []

#################### end of configuration section ####################

# contains only optional keys
default_mapping = {
    "only-update": True,
    "delete-before": False,
    "find-params": "-type f -print",
}

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
        for i in range(len(self.mappings)):
            # fill in missing optionals
            self.mapping = default_mapping.copy()
            self.mapping.update(self.mappings[i])

            print("Syncing %s" % self.mapping["src"])

            # handle delete-before
            if self.mapping["delete-before"] and os.path.exists(self.mapping["git"]):
                shutil.rmtree(self.mapping["git"])

            del self.files[:]   # clear list in case of repeated use
            self.find()
            self.filter()
            self.copy()

    def find(self):
        # convert to absolute path
        self.mapping["src"] = os.path.abspath(os.path.expanduser(self.mapping["src"]))

        if self.mapping["only-update"]:
            # <src>, <dest> is swapped
            cmd = "find %s  %s" % ( self.mapping["git"], self.mapping["find-params"] )
            dest_files = subprocess.check_output(cmd, shell=True, universal_newlines=True).splitlines()
            src_files = [remap(f, self.mapping["git"], self.mapping["src"]) for f in dest_files]
        else:
            # normal behavior
            cmd = "find %s  %s" % ( self.mapping["src"], self.mapping["find-params"] )
            src_files = subprocess.check_output(cmd, shell=True, universal_newlines=True).splitlines()
            dest_files = [remap(f, self.mapping["src"], self.mapping["git"]) for f in src_files]

        self.files.extend(list(zip(src_files, dest_files)))

    def filter(self):
        def matches(reobjects, fname):
            for reobj in reobjects:
                if reobj.match(fname):
                    return True
            return False

        for item in self.files[:]:  # slicing makes copy
            src = item[0]
            dest = item[1]

            # don't remove if in whitelist
            if matches(whitelist, src):
                print("Whitelisted %s" % src)
                continue

            # remove if in blacklist
            if matches(blacklist, src):
                print("Blacklisted %s" % src)
                self.files.remove(item)
                continue

            # remove if up-to-date (and both 'src' and 'dest' exist, otherwise we can't calculate hash)
            if os.path.exists(src) and os.path.exists(dest):
                if fhash(src) == fhash(dest) and os.path.getmtime(src) <= os.path.getmtime(dest):
                    self.files.remove(item)

    def copy(self):
        for item in self.files:
            src = item[0]
            dest = item[1]

            # display warning about non-existent files
            if not os.path.exists(src):
                print("WARNING: file doesn't exist: %s" % src)
                continue

            print("Copying %s\n    to %s" % (src, dest))
            try:
                os.makedirs(os.path.dirname(dest))
                shutil.copystat(os.path.dirname(src), os.path.dirname(dest))
            except OSError as e:
                if e.errno != 17:
                    raise

            if os.path.islink(src):
                linkto = os.readlink(src)
                os.symlink(linkto, dest)
            else:
                shutil.copy2(src, dest)


if __name__ == "__main__":
    # change to repo dir
    os.chdir(os.path.expanduser(repo_path))

    # translate white/black lists into regex objects
    whitelist = [re.compile(fnmatch.translate(os.path.expanduser(pattern))) for pattern in whitelist]
    blacklist = [re.compile(fnmatch.translate(os.path.expanduser(pattern))) for pattern in blacklist]

    sync = Sync(mappings, whitelist, blacklist)
    sync.run()
