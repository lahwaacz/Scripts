#! /usr/bin/env python3

"""
THE BEER-WARE LICENSE (Revision 42):
Jakub Klinkovský wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.
"""

import argparse
import os.path
import datetime
import sys

# maybe depends on the locale in which MS Teams runs...
TIMESTAMP_FORMATS = [
    "%m/%d/%Y, %I:%M:%S %p",
    "%d. %m. %Y %H:%M:%S",
]

CLASS_LENGTH = datetime.timedelta(minutes=100)

def parse_timestamp(timestamp):
    last_error = None
    for format in TIMESTAMP_FORMATS:
        try:
            return datetime.datetime.strptime(timestamp, format)
        except ValueError as e:
            last_error = e
            continue
    raise last_error

def parse_attendance_list(path):
    print(f"Parsing file {path}...")
    data = {}
    text = open(path, "r", encoding="utf-16").read()

    for line in text.splitlines():
        # parse items on the line
        name, action, timestamp = line.split("\t")
        # skip header line
        if name == "Full Name" or name == "Celé jméno":
            continue

        # validate items
        assert "," in name, name
        assert action in {"Joined", "Left", "Připojeno", "Odpojil(a) se"}, f"unknown action: {action}"
        timestamp = parse_timestamp(timestamp)

        # initialize data
        user_actions = data.setdefault(name, [])

        # append action
        user_actions.append((action, timestamp))

    return data

def get_attendance(class_start, actions):
    class_end = class_start + CLASS_LENGTH

    # make sure actions are sorted by timestamp
    actions.sort(key=lambda a: a[1])

    # calculate
    attendance = datetime.timedelta()
    joined = None
    for i, item in enumerate(actions):
        action, timestamp = item
        if action in {"Joined", "Připojeno"}:
            assert joined is None
            joined = timestamp
        elif action in {"Left", "Odpojil(a) se"}:
            assert joined is not None
            attendance += timestamp - joined
            joined = None
        else:
            assert False
    # handle the missing "Left" action
    if joined is not None:
        attendance += class_end - joined

    return attendance

def print_attendance(teacher, class_start, data):
    print(f"Class teacher:\t{teacher}")
    print(f"Class start:\t{class_start}")
    print("Attendance:")

    for name in sorted(data.keys()):
        attendance = get_attendance(class_start, data[name])
        perc = attendance.seconds / CLASS_LENGTH.seconds * 100
        print(f"   {name:<30}\t{attendance} ({perc:.0f}%)")

    print()

def main(path):
    data = parse_attendance_list(path)
    teacher = list(data.keys())[0]
    class_start = data[teacher][0][1]
    del data[teacher]
    print_attendance(teacher, class_start, data)

parser = argparse.ArgumentParser(description="parser for MS Teams attendance list files")
parser.add_argument("path", nargs="+", help="path to the attendance list file")

args = parser.parse_args()
for p in args.path:
    if os.path.isfile(p):
        main(p)
    else:
        print(f"ERROR: {p} is not a file", file=sys.stderr)
