#! /usr/bin/env python

import sys
import os
import traceback

CHARSETS = ("ascii", "cp1250", "cp1252", "iso-8859-9", "iso-8859-15")

def is_utf8(filepath):
    try:
        file = open(filepath, "rb")
        file.read().decode('utf-8')
        file.close()
        return True
    except:
        return False
    
def to_utf8(path):
    for charset in CHARSETS:
        try:
            f = open(path, 'rb')
            content = f.read().decode(charset)
            f.close()
            f = open(path, 'wb')
            f.write(content.encode('utf-8'))
            f.close()
            return "Converting to utf-8: " + os.path.split(path)[1]
        except:
            pass
    return "Unable to open " + os.path.split(path)[1] + " - unknown charset or binary file."

def run():
    message = ""
    for filename in sys.argv[1:]:
        if os.path.isfile(filename):
            if is_utf8(filename):
                message += os.path.split(filename)[1] + " is already in utf-8.\n"
            else:
                message += to_utf8(filename) + "\n"
    return message.strip()
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: " + sys.argv[0] + " file1 [file2 ...]")
        sys.exit(1)
        
    try:
        message = run()
    except:
        message = traceback.format_exc()
    if message != "":
        print(message)
