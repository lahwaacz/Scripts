#! /usr/bin/env python

import sys
import os
import argparse
import re


class Main:
    def __init__(self, args):
        self.root = os.path.abspath(args.root[0])
        self.filterRe = args.filter[0]
        self.matchRe = args.match[0]
        self.renamePattern = args.rename[0]

        self.files = []

        self.check()

    def check(self):
        msg = ""

        # check filtering regular expression
        try:
            re.match(self.filterRe, "")
        except:
            msg = "Invalid filtering regular expression: " + self.filterRe

        # check matching regular expression
#        try:
#            re.match(self.matchRe, "")
#        except:
#            msg = "Invalid matching regular expression: " + self.matchRe

        # TODO: check self.renamePattern

        if msg != "":
            print("Error: " + msg)
            sys.exit(1)

    def browse(self, path):
        for file in os.listdir(path):
            absPath = os.path.join(path, file)
            dirname, fname = os.path.split(absPath)
            if os.path.isdir(absPath):
                self.browse(absPath)
            elif os.path.isfile(absPath):
                self.files.append({"dirname":dirname, "fname":fname, "abspath":absPath, "filtered":False, "matchdict":{}, "newfname":""})

    def filter(self):
        self.files.sort(key=lambda d: d["abspath"])
        for item in self.files:
            if re.match(self.filterRe, item["fname"]):
                item["filtered"] = True

    def match(self):
        for item in self.files:
            if item["filtered"] is True:
                regex = re.compile(self.matchRe)
                search = regex.search(item["fname"])
                if search is not None:
                    item["matchdict"] = search.groupdict()
                else:
                    print("No match: " + item["fname"])

    def newname(self):
        for item in self.files:
            if item["matchdict"]:
                item["newfname"] = self.renamePattern.replace("{", "{0[").replace("}", "]}").format(item["matchdict"])

    def preview(self):
        for item in self.files:
            if item["filtered"] and item["matchdict"]:
                old = item["abspath"]
                new = os.path.join(item["dirname"], item["newfname"])
                print("  " + old + "\n      => " + new)

    def rename(self):
        for item in self.files:
            if item["filtered"] and item["matchdict"]:
                old = item["abspath"]
                new = os.path.join(item["dirname"], item["newfname"])
                print("  " + old + "\n      => " + new)
                stat = os.stat(old)
                os.rename(old, new)
                os.utime(new, (stat.st_atime, stat.st_mtime))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="rename whole series to match selected pattern")
    parser.add_argument("root", action="store", nargs=1, help="root directory of the series")
    parser.add_argument("-f", "--filter", action="store", dest="filter", nargs=1, help="filtering regular expression")
    parser.add_argument("-m", "--match", action="store", dest="match", nargs=1, help="matching regular expression")
    parser.add_argument("-r", "--rename", action="store", dest="rename", nargs=1, help="renaming pattern")
    parser.add_argument("--preview", action="store_true", help="preview only - don't rename the files")

    args = parser.parse_args()

    main = Main(args)
    main.browse(main.root)
    main.filter()
    main.match()
    main.newname()
    if args.preview:
        main.preview()
    else:
        main.rename()
        print("All files succesfully renamed.")
