#! /usr/bin/env python3

import subprocess
import json

data = {}

cmd = [
    "khal",
    "list",
    "now",
    "23:59",
    "--once",
    "--format",
    "{start-time} ({location}) {title}{repeat-symbol}{alarm-symbol}",
]
output = subprocess.run(cmd, check=True, text=True, capture_output=True).stdout

lines = [line.strip() for line in output.split("\n")]

# filter out lines that do not start with a number
# (khal list includes headings like "Monday, 2025-03-31" for each day)
lines = [line for line in lines if line and line[0].isdigit()]

if lines:
    data["text"] = " " + lines[0]
    data["tooltip"] = "\n".join(lines)
else:
    data["text"] = ""

print(json.dumps(data))
