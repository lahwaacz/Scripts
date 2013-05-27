#! /usr/bin/env python

import os
import sys
import argparse

def main(dir, prefix, suffix):
    avis = []
    subtitles = []

    for fname in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, fname)):
            ext = os.path.splitext(fname)[1]
            if ext == ".avi":
                avis.append(fname)
            elif ext in [".sub", ".srt"]:
                if fname.startswith(prefix):
                    subtitles.append(fname)

    if len(avis) == len(subtitles):
        avis.sort()
        subtitles.sort()

        for i in range(len(avis)):
            basename = os.path.splitext(avis[i])[0]
            ext = os.path.splitext(subtitles[i])[1]
            old = os.path.join(dir, subtitles[i])
            new = os.path.join(dir, basename + suffix + ext)
            print(old + " => " + new)
            os.rename(old, new)
    else:
        print("Error: len(avis) != len(subtitles)")
        raise Exception

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="rename subtitles in directory to match name of their video file")
    parser.add_argument("directory", action="store", nargs=1, help="directory path")
    parser.add_argument("-p", "--prefix", action="store", dest="prefix", nargs=1, required=True, help="select only subtitles starting with prefix")
    parser.add_argument("-s", "--suffix", action="store", dest="suffix", nargs=1, required=True, help="add suffix to subtitle name when renaming")

    args = parser.parse_args()

    main(args.directory[0], args.prefix[0], args.suffix[0])
