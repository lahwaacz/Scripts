#! /usr/bin/env python

# Little script to "touch" directory structure.
# Works like 'cp -r', but instead of copying full file, the new file is "touched",
# so the tree structure is preserved and only empty files created.

import sys
import os


class Main:
    def __init__(self, oldRoot, newRoot):
        self.oldRoot = oldRoot
        self.newRoot = newRoot

    def browse(self, path):
        for file in os.listdir(path):
            absPath = os.path.join(path, file)
            relPath = os.path.relpath(absPath, self.oldRoot)
            if os.path.isdir(absPath):
                os.mkdir(os.path.join(self.newRoot, relPath))
                self.browse(absPath)
            elif os.path.isfile(absPath):
                open(os.path.join(self.newRoot, relPath), "w").close()

    def touchTree(self):
        os.mkdir(newRoot)
        self.browse(self.oldRoot)

if len(sys.argv) != 3 or not os.path.isdir(sys.argv[1]) or os.path.exists(sys.argv[2]):
    sys.exit(1)

oldRoot = os.path.abspath(sys.argv[1])
newRoot = os.path.abspath(sys.argv[2])

print(oldRoot + "  =>  " + newRoot)
main = Main(oldRoot, newRoot)
main.touchTree()
