#! /usr/bin/env python3

import os
import argparse
import configparser
import subprocess

CONFIG = os.path.expanduser("~/.config/fmount.conf")
DEFAULT_MOUNTPATH = os.path.expanduser("~/mnt")

# we just strip spaces in the mntopts string
def reformat_mntopts(mntopts):
    mntopts = mntopts.split(",")
    options = []
    for opt in mntopts:
        options.append("=".join(tk.strip() for tk in opt.split("=")))
    return ",".join(set(options))

def mount(name, mountpath, config):
    mountpoint = os.path.join(mountpath, name)
    host = config.get(name, "host", fallback=name)
    path = config.get(name, "path", fallback="")
    user = config.get(name, "user", fallback=None)
    port = config.get(name, "port", fallback=None)
    mntopts = config.get(name, "mntopts", fallback=[])
    mntopts = reformat_mntopts(mntopts)

    uhd = host + ":" + path
    if user:
        uhd = user + "@" + uhd

    cmd = ["sshfs", uhd, mountpoint]
    if mntopts:
        cmd += ["-o", mntopts]
    if port:
        cmd += ["-p", port]

    print("Mounting at '{}'...".format(mountpoint))
    # the mountpoint might exist after an error or automatic unmount
    try:
        os.makedirs(mountpoint)
    except FileExistsError:
        pass
    subprocess.run(cmd, check=True)

def umount(mntpoint):
    if os.path.ismount(path):
        cmd = ["fusermount", "-u", mntpoint]
        subprocess.run(cmd, check=True)
    clean(mntpoint)

def clean(path):
    if not os.path.ismount(path) and len(os.listdir(path)) == 0:
        print("Removing empty mountpoint '{}'...".format(path))
        os.rmdir(path)

def cleanAll(mountpath):
    for file in os.listdir(mountpath):
        path = os.path.join(mountpath, file)
        if os.path.isdir(path):
            clean(path)

def writeDefaultConfig():
    cfile = open(CONFIG, mode="w", encoding="utf-8")
    print("""\
# globals live in the DEFAULT section
[DEFAULT]
mountpath = {mountpath}
#mntopts = opt1=val1, opt2=val2, ... # optional

#[remote_name]
#host = ... # optional, equal to remote_name by default
#path = ... # optional, sshfs defaults to remote $HOME
#user = ... # optional, .ssh/config is honoured
#port = ... # optional, .ssh/config is honoured
#mntopts = opt1=val1, opt2=val2, ... # optional""".format(mountpath=DEFAULT_MOUNTPATH), file=cfile)
    cfile.close()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG):
        writeDefaultConfig()
    config.read(CONFIG)

    parser = argparse.ArgumentParser(description="wrapper for sshfs with a config file")
    parser.add_argument("-u", action="store_true", dest="umount", help="unmount given host or path")
    parser.add_argument("host", nargs="+", help="remote name specified in the config file")
    args = parser.parse_args()

    mountpath = os.path.expanduser(config.get("DEFAULT", "mountpath", fallback=DEFAULT_MOUNTPATH))

    if args.umount:
        for host in args.host:
            if os.path.isdir(host):
                # not a host, but a path
                path = host
            else:
                path = os.path.join(mountpath, host)
                if not os.path.isdir(path):
                    parser.error("Path '{}' does not exist.".format(path))
            if os.path.ismount(path):
                umount(path)
            else:
                parser.error("Path '{}' is not a mount point.".format(path))
    else:
        for host in args.host:
            if config.has_section(host):
                if os.path.ismount(os.path.join(mountpath, host)):
                    parser.error("Host '{}' is already mounted.".format(host))
                mount(host, mountpath, config)
            else:
                parser.error("Section '{}' does not exist in the config file.".format(host))
    cleanAll(mountpath)
