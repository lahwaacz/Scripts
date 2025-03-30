#! /usr/bin/env python3

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path

CONFIG = Path.home() / ".config" / "fmount.conf"
DEFAULT_MOUNTPATH = Path.home() / "mnt"


# we just strip spaces in the mntopts string
def reformat_mntopts(mntopts):
    mntopts = mntopts.split(",")
    options = []
    for opt in mntopts:
        options.append("=".join(tk.strip() for tk in opt.split("=")))
    return ",".join(set(options))


def mount_gio(*, scheme: str, host: str, path: str, user: str, port: str, mountpoint: Path):
    if mountpoint.exists() and not mountpoint.is_symlink():
        print(f"Error: path {mountpoint} exists but is not a symlink", file=sys.stderr)
        return

    location = f"{scheme}://"
    if user:
        location += user + "@"
    location += host
    if port:
        location += ":" + port
    location += "/" + path

    # get path to thet gvfs directory
    XDG_RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR")
    if XDG_RUNTIME_DIR is None:
        XDG_RUNTIME_DIR = f"/run/user/{os.getuid()}"
    gvfs = Path(XDG_RUNTIME_DIR) / "gvfs"

    # save current gvfs mounts
    if gvfs.is_dir():
        mounts_before = set(gvfs.glob(f"{scheme}-share:*"))
    else:
        mounts_before = set()

    print(f"Mounting {location}")
    cmd = ["gio", "mount", location]
    subprocess.run(cmd, check=True)

    if not gvfs.is_dir():
        print(f"Error: gvfs directory {gvfs} does not exist", file=sys.stderr)
        return

    # detect the new gvfs mount symlink it to mountpoint
    mounts_after = set(gvfs.glob(f"{scheme}-share:*"))
    target = list(mounts_after - mounts_before)[0]

    # hack for inaccessible parents of the path on smb servers
    if scheme == "smb":
        _path = Path(path.lstrip("/"))
        # the first part is the remote share, the rest is the location we want
        target /= _path.relative_to(_path.parts[0])

    # create a symlink from mountpoint to gvfs target
    mountpoint.symlink_to(target)


def mount_sshfs(*, host: str, path: str, user: str, port: str, mountpoint: Path, mntopts: str):
    uhd = host + ":" + path
    if user:
        uhd = user + "@" + uhd

    cmd = ["sshfs", uhd, str(mountpoint)]
    if mntopts:
        cmd += ["-o", mntopts]
    if port:
        cmd += ["-p", port]

    print(f"Mounting at '{mountpoint}'...")
    # the mountpoint might exist after an error or automatic unmount
    mountpoint.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)


def mount(name, mountpath: Path, config):
    mountpoint = mountpath / name
    scheme = config.get(name, "scheme", fallback="sshfs")
    host = config.get(name, "host", fallback=name)
    path = config.get(name, "path", fallback="")
    user = config.get(name, "user", fallback=None)
    port = config.get(name, "port", fallback=None)
    mntopts = config.get(name, "mntopts", fallback="")
    mntopts = reformat_mntopts(mntopts)

    if scheme == "sshfs":
        # sshfs is *much* faster than gvfs
        return mount_sshfs(
            host=host,
            path=path,
            user=user,
            port=port,
            mountpoint=mountpoint,
            mntopts=mntopts,
        )
    else:
        return mount_gio(
            scheme=scheme,
            host=host,
            path=path,
            user=user,
            port=port,
            mountpoint=mountpoint,
        )


def umount(mntpoint: Path):
    if path.is_mount():
        cmd = ["fusermount3", "-u", str(mntpoint)]
        subprocess.run(cmd, check=True)
        clean(mntpoint)
    elif path.is_symlink():
        if path.readlink().exists():
            cmd = ["gio", "mount", "--unmount", str(mntpoint.resolve())]
            subprocess.run(cmd, check=True)
        # do not call clean(path), gio takes a while to remove the target
        path.unlink()
    elif path.is_dir():
        print(f"Note: directory '{path}' is not a mount point.", file=sys.stderr)
        return


def clean(path: Path):
    if path.is_symlink() and not path.readlink().exists():
        print(f"Removing broken symlink '{path}'...")
        path.unlink()
    else:
        if not path.is_mount() and not any(path.iterdir()):
            print(f"Removing empty mountpoint '{path}'...")
            path.rmdir()


def cleanAll(mountpath):
    for file in mountpath.iterdir():
        path = mountpath / file
        if path.is_dir():
            clean(path)


def writeDefaultConfig():
    with open(CONFIG, mode="w", encoding="utf-8") as cfile:
        print(
            f"""\
# globals live in the DEFAULT section
[DEFAULT]
mountpath = {DEFAULT_MOUNTPATH}
#mntopts = opt1=val1, opt2=val2, ... # optional

#[remote_name]
#scheme = ... # optional, either sshfs (default) or anything else supported by gvfs
#host = ... # optional, equal to remote_name by default
#path = ... # optional, sshfs defaults to remote $HOME
#user = ... # optional, .ssh/config is honoured
#port = ... # optional, .ssh/config is honoured
#mntopts = opt1=val1, opt2=val2, ... # optional
""",
            file=cfile,
        )


if __name__ == "__main__":
    config = configparser.ConfigParser()
    if not CONFIG.exists():
        writeDefaultConfig()
    config.read(CONFIG)

    parser = argparse.ArgumentParser(
        description="wrapper for sshfs and gio with a config file"
    )
    parser.add_argument(
        "--list-available",
        action="store_true",
        help="list the hosts defined in the configuration file and exit",
    )
    parser.add_argument(
        "--list-mounted",
        action="store_true",
        help="list the currently mounted hosts and exit",
    )
    parser.add_argument(
        "-u", "--unmount", action="store_true", help="unmount given host or path"
    )
    parser.add_argument(
        "host", nargs="*", help="remote name(s) specified in the config file"
    )
    args = parser.parse_args()

    mountpath = Path(
        os.path.expanduser(
            config.get("DEFAULT", "mountpath", fallback=DEFAULT_MOUNTPATH)
        )
    )

    if args.list_available:
        hosts = set(key for key in config.keys() if key != "DEFAULT")
        for host in sorted(hosts):
            print(host)

    elif args.list_mounted:
        for file in sorted(mountpath.iterdir()):
            print(file.name)

    else:
        if args.host:
            for host in args.host:
                if args.unmount:
                    if Path(host).is_dir():
                        # not a host, but a path
                        path = Path(host)
                    else:
                        path = mountpath / host
                        if not path.exists():
                            print(
                                f"Note: path '{path}' does not exist.", file=sys.stderr
                            )
                    umount(path)
                else:
                    if config.has_section(host):
                        if (mountpath / host).is_mount():
                            parser.error(f"Host '{host}' is already mounted.")
                        mount(host, mountpath, config)
                    else:
                        parser.error(
                            f"Section '{host}' does not exist in the config file."
                        )
        else:
            parser.error("No hosts were given.")
        cleanAll(mountpath)
