#! /usr/bin/env python3

def cores_count():
    f = open("/proc/cpuinfo")
    for line in f.readlines():
        if line.startswith("cpu cores"):
            try:
                _, n = line.split(":")
                return int(n.strip())
            except ValueError:
                continue
    return 1
