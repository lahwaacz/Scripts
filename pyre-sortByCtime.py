#! /usr/bin/env python

import os
import sys
import argparse
import time
import subprocess
import re
import threading

from ffparser.ffparser import FFprobeParser
from ffparser.process_utils import getstatusoutput


# ffprobe doesn't work for images
def getCreationTimeHachoir(fpath):
    status, output = getstatusoutput("hachoir-metadata --raw --level 5 " + re.escape(fpath))
    if status == 0:
        ctime = None
        for line in output.splitlines():
            if line.strip().startswith("- creation_date:"):
                ctime = " ".join(line.split()[-2:]) 
                ctime = time.mktime(time.strptime(ctime, "%Y-%m-%d %H:%M:%S"))
                break
        if ctime:
            return ctime
        else:
            raise Exception
    else:
        raise Exception

def getCreationTimeFFprobe(fpath):
    ffparser = FFprobeParser(fpath)
    ctime = ffparser.get("format", "tags")["creation_time"]
    ctime = time.mktime(time.strptime(ctime, "%Y-%m-%d %H:%M:%S"))
    if ctime:
        return ctime
    else:
        raise Exception

def getCreationTime(fpath):
    try:
        return getCreationTimeFFprobe(fpath)
    except:
        pass

    try:
        return getCreationTimeHachoir(fpath)
    except:
        pass

    # useful only when ffprobe or hachoir are not installed
    return os.path.getmtime(fpath)


class Main:
    def __init__(self, dir, order, preview):
        self.directory = dir
        if order == "ascending":
            self.reverse = False
        elif order == "descending":
            self.reverse = True
        self.preview = preview

        self.files = []
        self.threadBuffer = []

        self.threads = 2
        self.killed = False
        self.threadsFinished = 0
        self.lock = threading.Lock()

    def run(self):
        # fill buffer
        for fname in os.listdir(self.directory):
            fpath = os.path.join(self.directory, fname)
            if os.path.isfile(fpath):
                self.threadBuffer.append(fpath)
        self.threadBuffer.sort()

        # start threads
        for i in range(self.threads):
            v = threading.Thread(target=self.worker, args=(i + 1,))
            v.start()

        # wait for threads to finish
        try:
            while self.threadsFinished < self.threads:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.killed = True
            print("Interrupt signal received, exiting...")
            sys.exit(1)

        # do additional work
        self.files.sort(key=lambda x: x["key"], reverse=self.reverse)
        digits = len(str(len(self.files)))
        for i in range(len(self.files)):
            self.files[i]["num"] = (digits - len(str(i+1))) * "0" + str(i+1)

            # generate new file name
            old = self.files[i]["fpath"]
            dir, fname = os.path.split(self.files[i]["fpath"])
            num = self.files[i]["num"]
            new = os.path.join(dir, num + " " + fname)

            # preview
            print(num + "    " + fname)

            if not self.preview:
                os.rename(old, new)

    def worker(self, id):
        while not self.killed:
            try:
                self.lock.acquire()
                fpath = self.threadBuffer.pop(0)
                self.lock.release()

                ctime = getCreationTime(fpath)
                self.files.append({"fpath":fpath, "key":ctime, "num":None})
            except IndexError:
                self.lock.release()
                break
            else:
                if not self.killed:
                    print("Thread " + str(id) + ": " + fpath)
        self.threadsFinished += 1



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="rename all files in directory, sorted by creation time (ffprobe required for audio and video, hachoir-metadata for images)")
    parser.add_argument("directory", action="store", nargs=1, help="directory path")
    parser.add_argument("--order", action="store", dest="order", nargs="?", choices=["ascending", "descending"], default="ascending", help="sort order, ascending by default")
    parser.add_argument("--preview", action="store_true", default=False, dest="preview", help="don't rename, only preview")

    args = parser.parse_args()

    main = Main(args.directory[0], args.order, args.preview)
    main.run()
