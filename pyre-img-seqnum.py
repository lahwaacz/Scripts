#! /usr/bin/env python

import os
import sys
import argparse
import re
import fnmatch
import shutil

ACTIONS = ("seqnum", "insert")

def natural_sort(l): 
    """ Sort the given list in the way that humans expect. 
        For example: ["img_1", "img_2", "img_3", "img_20"]
        instead of ["img_1", "img_2", "img_20", "img_3"]
    """ 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    l.sort(key=alphanum_key) 

def move_file(src, dst):
    if src != dst:
        print("mv '%s' '%s'" % (src, dst))
        if not os.path.exists(dst):
#            shutil.move(src, dst)
        else:
            print("warning: file exists: %s" % dst)
    else:
        print("correct: '%s'" % src)

def seqnum(files, pattern):
    for f in files:
        i = files.index(f) + 1
        new = pattern % i
        move_file(f, new)

def insert(files, pattern, to_insert, index):
    assert((to_insert in files) == False)
    files.insert(index - 1, to_insert)
    seqnum(files, pattern)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="very simple tool for renaming images")
    parser.add_argument("pattern", action="store", help="Formatting pattern to rename the files, the index of the file in list is passed. For example 'img_%%03d.jpg'")
    parser.add_argument("--filter", action="store", default="*", help="Only files that pass this filter are added to the list of files. Uses simple shell globbing through fnmatch module.")
    actions = parser.add_subparsers(title="actions", dest="action")

    parser_seqnum = actions.add_parser("seqnum", help="Rename all files in current directory according to specified pattern.")

    parser_insert = actions.add_parser("insert", help="Insert specified file into specified position, then rename the files.")
    parser_insert.add_argument("to_insert", action="store", help="The name of the file to insert into list.")
    parser_insert.add_argument("index", action="store", type=int, help="Index in the file list at which the file will be inserted.")

    args = parser.parse_args()

    args.filter = re.compile(fnmatch.translate(os.path.expanduser(args.filter)))

    files = os.listdir(".")
    files = [x for x in files if args.filter.match(x)]
    natural_sort(files)

    if args.action == "seqnum":
        seqnum(files, args.pattern)
    elif args.action == "insert":
        insert(files, args.pattern, args.to_insert, args.index)

#    print(args)
#    print(files)
