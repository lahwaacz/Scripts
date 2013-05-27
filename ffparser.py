#! /usr/bin/env python

import argparse

from pythonscripts.ffparser import FFprobeParser


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="parse ffprobe's json output")

    option = parser.add_mutually_exclusive_group(required=True)
    option.add_argument("-a", "--audio", action="store_const", const="audio", dest="option", help="get audio attribute")
    option.add_argument("-v", "--video", action="store_const", const="video", dest="option", help="get video attribute")
    option.add_argument("-f", "--format", action="store_const", const="format", dest="option", help="get format attribute")

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("-g", "--get", action="store", nargs=1, dest="attribute", help="attribute name to get")
    action.add_argument("-p", "--print", action="store_true", dest="pprint", help="print all attributes and exit")

    parser.add_argument("path", action="store", nargs=1, help="path to file to parse")

    args = parser.parse_args()
    ffparser = FFprobeParser(args.path[0])
    if args.pprint:
        ffparser.pprint(args.option)
    else:
        print(ffparser.get(args.option, args.attribute[0]))
