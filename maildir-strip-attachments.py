#!/usr/bin/env python3

# Documentation:
# - https://docs.python.org/3/library/mailbox.html#mailbox.Maildir
# - https://docs.python.org/3/library/mailbox.html#mailbox.MaildirMessage

import os
import argparse
import mailbox

DROP_MIN_SIZE = 256  # KiB
DROP_CONTENT_TYPES = [
    "image/",
    "video/",
    "application/pdf",
    "application/x-extension-pdf",
    "application/zip",
    "application/gzip",
    "application/x-gzip",
    "application/x-xz",
    "application/x-7z-compressed",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/x-msdownload",
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/vnd.ms-xpsdocument",
    "application/octet-stream",
]

def process_maildir(maildir):
    dropped_items = 0
    dropped_size = 0

    mb = mailbox.Maildir(maildir, create=False)
    for key, message in mb.iteritems():
        for part in message.walk():
            if part.is_multipart():
                continue
            size = len(part.as_bytes()) / 1024
            if size > DROP_MIN_SIZE:
                print("{}\tsize: {:g} KiB".format(part.get_content_type(), size))
                for ct in DROP_CONTENT_TYPES:
                    if part.get_content_type().startswith(ct):
                        part.set_payload("")
                        dropped_items += 1
                        dropped_size += size

        # update the message on disk
        mb.update({key: message})

    print("Dropped {} attachements ({:g} MiB).".format(dropped_items, dropped_size / 1024))

def argtype_dir_path(string):
    if os.path.isdir(string):
        return string
    raise NotADirectoryError(string)

def argtype_maildir(string):
    string = argtype_dir_path(string)
    for sub in ["cur", "new", "tmp"]:
        subdir = os.path.join(string, sub)
        if not os.path.isdir(subdir):
            raise NotADirectoryError(subdir)
    return string

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Strip attachments from messages in a maildir.")
    ap.add_argument("maildir", metavar="PATH", type=argtype_maildir,
                    help="path to the maildir")

    args = ap.parse_args()
    process_maildir(args.maildir)
