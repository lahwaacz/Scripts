#! /usr/bin/env python

# converts Chromium bookmarks (usually in '~/.config/chromium/<profile>/Bookmarks') to format suitable for dwb

import json
import sys

def parse(js):
    if "url" in js.keys():
        print("%s %s" % (js["url"], js["name"]))
        return

    if "children" in js.keys():
        for child in js["children"]:
            parse(child)
        return

    for key, val in js.items():
        if isinstance(val, dict):
            parse(val)

bookmarks = json.load(open(sys.argv[1]))
parse(bookmarks)
