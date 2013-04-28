#!/usr/bin/env python

import sys
import os
import argparse
import configparser
import subprocess
import re


CONFIG = os.environ["HOME"] + "/.config/fmount.conf"
IDFNAME = ".created-by-fmount"
PROTOCOLS = ["file", "ftp", "ftps", "sftp"]
EXTENSIONS = [".iso", ".tar", ".taz", ".tbz", ".tbz2", ".tg", ".tgz", ".tz", ".tzl", ".tlzma", \
              ".gz", ".gzi", ".gzip", ".bz", ".bz2", ".bzip", ".bzip2", ".7z", ".xz", ".zip", ".rar"]
REGEX = {
    "file":
        "^((?P<protocol>file):/{0,2})?(?P<path>/[\S\ ]*)(" + "|".join(EXTENSIONS) + ")$",
    "url":
        "^(?P<protocol>" + "|".join(PROTOCOLS) + ")://" \
        "((?P<username>[a-z0-9_]{3,15})@)?" \
        "((?P<ipaddress>((\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5])\.){3}(\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5]))|" \
        "(?P<hostname>(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])))" \
        "(:(?P<port>\d+))?" \
        "(?P<path>/\S*)?$",
}

#ValidIpAddressRegex = "^((\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5])\.){3}(\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5])$"
#ValidHostnameRegex = "^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$"
#ValidMacAddressRegex = "^(([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})|" \
#"([0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}))$"

##/^(https?|ftp):\/\/(?#                                      protocol
##)(([a-z0-9$_\.\+!\*\'\(\),;\?&=-]|%[0-9a-f]{2})+(?#         username
##)(:([a-z0-9$_\.\+!\*\'\(\),;\?&=-]|%[0-9a-f]{2})+)?(?#      password
##)@)?(?#                                                     auth requires @
##)((([a-z0-9]\.|[a-z0-9][a-z0-9-]*[a-z0-9]\.)*(?#            domain segments AND
##)[a-z][a-z0-9-]*[a-z0-9](?#                                 top level domain  OR
##)|((\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5])\.){3}(?#
##    )(\d|[1-9]\d|1\d{2}|2[0-4][0-9]|25[0-5])(?#             IP address
##))(:\d+)?(?#                                                port
##))(((\/+([a-z0-9$_\.\+!\*\'\(\),;:@&=-]|%[0-9a-f]{2})*)*(?# path
##)(\?([a-z0-9$_\.\+!\*\'\(\),;:@&=-]|%[0-9a-f]{2})*)(?#      query string
##)?)?)?(?#                                                   path and query string optional
##)(#([a-z0-9$_\.\+!\*\'\(\),;:@&=-]|%[0-9a-f]{2})*)?(?#      fragment
##)$/i


def xstr(s):
    return s or ""

def getMessageAliases():
    msg = ""
    items = sorted(config["aliases"].items())
    for item in items:
        msg += " = ".join(item) + "\n"
    return msg

def getMessageExtensions():
    return ", ".join(EXTENSIONS)

def getMessageProtocols():
    return ", ".join(x + "://" for x in PROTOCOLS)


class PrintMessageAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None,
                 message=""):
        super(PrintMessageAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.message = message

    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_text(self.message)
        parser.exit(message=formatter.format_help())


def getter_setter_gen(name, type_):
    def getter(self):
        return getattr(self, "__" + name)
    def setter(self, value):
        if not isinstance(value, type_):
            raise TypeError("%s attribute must be set to an instance of %s" % (name, type_))
        setattr(self, "__" + name, value)
    return property(getter, setter)

def auto_attr_check(cls):
    new_dct = {}
    for key, value in cls.__dict__.items():
        if isinstance(value, type):
            value = getter_setter_gen(key, value)
        new_dct[key] = value
    # Creates a new class, using the modified dictionary as the class dict:
    return type(cls)(cls.__name__, cls.__bases__, new_dct)


@auto_attr_check
class Mount():
    url = str
    options = []
    mntpoint = str
    
    protocol = str
    username = str
    host = str
    port = str
    path = str
    
    def __init__(self, url, options):
        self.url = url
        if options:
            self.options = options[0].split(",")
        self.mntpoint = ""
        
        self.parseUrl()
        self.createMntpoint()
        self.mount()

    def parseUrl(self):
        for regex in REGEX.values():
            if re.match(regex, self.url):
                urlDict = re.compile(regex).search(self.url).groupdict()
                break
        else:
            parser.error("invalid URL or unsupported protocol")
        
        self.protocol = xstr(urlDict["protocol"])
        if self.protocol == "":
            self.protocol = "file"
        self.username = xstr(urlDict["username"])
        self.host = xstr(urlDict["hostname"])
        if self.host == "":
            self.host = xstr(urlDict["ipaddress"])
        self.port = xstr(urlDict["port"])
        self.path = xstr(urlDict["path"])
        
    def mount(self):
        if self.protocol == "sftp":
            src = "@".join(filter(None, [self.username, self.host])) + ":" + self.path
        elif self.protocol == "file":
            src = path
        else:
            src = self.url
        
        if self.protocol == "ftps":
            self.options.append("ssl")
        
        if self.port:
            self.options.append("port="+self.port)
        
        # for all protocols; there's file IDFNAME in mntpoint already
        self.options.append("nonempty")

        options = ",".join(set(self.options))
        if options:
            options = "-o " + options
        
        cmd = " ".join((config["backends"][self.protocol], options, re.escape(src), re.escape(self.mntpoint)))
        popen = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        status = popen.wait()
        output = popen.stdout.read()
        if status > 0:
            parser.error("mount failed:\n" + output)
            os.rmdir(self.mntpoint)

    def createMntpoint(self):
        if self.protocol != "file":
            dirname = self.protocol + "-" + "@".join(filter(None, [self.username, self.host]))
        else:
            dirname = "archive-" + self.getArchiveNumber()
        self.mntpoint = os.path.join(config["main"]["MainPath"], dirname)
        if os.path.exists(self.mntpoint):
            parser.error(dirname + " is already mounted")
        else:
            os.makedirs(self.mntpoint)
            open(os.path.join(self.mntpoint, IDFNAME), "w").close()
    
    def getArchiveNumber():
        mounts = open("/proc/mounts", "r")
        mounted = mounts.readlines()
        mounts.close()
        fuse_mounts = 0
        for line in mounted:
            if config["main"]["MainPath"] in line and line.split()[1].startswith("archive"):
                fuse_mounts += 1
        return fuse_mounts

    
def umount(mntpoint, options=""):
    if not clean(mntpoint):
        if options:
            options = "-o " + options
        cmd = "fusermount -u " + xstr(options) + " " + re.escape(mntpoint)
        popen = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        status = popen.wait()
        output = popen.stdout.read()
        if status > 0:
            parser.error("umount failed:\n" + output)
        else:
            clean(mntpoint)

def clean(path):
    if os.listdir(path) == [IDFNAME]:
        os.remove(os.path.join(path, IDFNAME))
        os.rmdir(path)
        return True
    else:
        return False

def cleanAll():
    for file in os.listdir(config["main"]["MainPath"]):
        path = os.path.join(config["main"]["MainPath"], file)
        if not os.path.ismount(path) and os.path.isdir(path):
            clean(path)

def writeDefaultConfig():
    cfile = open(CONFIG, mode="w", encoding="utf-8")
    print("[main]", file=cfile)
    print("MainPath = " + os.environ["HOME"] + "/mnt", file=cfile)
    print("", file=cfile)
    print("[backends]", file=cfile)
    print("file = archivemount", file=cfile)
    print("ftp = curlftpfs", file=cfile)
    print("ftps = curlftpfs", file=cfile)
    print("sftp = sshfs", file=cfile)
    print("", file=cfile)
    print("[aliases]", file=cfile)
    print("", file=cfile)
    cfile.close()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG):
        writeDefaultConfig()
    config.read(CONFIG, "utf-8")
    
    if not os.path.exists(config["main"]["MainPath"]):
        os.mkdir(config["main"]["MainPath"])
    os.chdir(config["main"]["MainPath"])
    
    parser = argparse.ArgumentParser(
                usage='%(prog)s [-h] [-aep] [-u mntpoint] file | URL | alias',
                description="simple wrapper for FUSE to create mountpoints in one directory",
                formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-a", action=PrintMessageAction, help="print aliases from config file", message=getMessageAliases())
    parser.add_argument("-e", action=PrintMessageAction, help="print supported file extensions", message=getMessageExtensions())
    parser.add_argument("-p", action=PrintMessageAction, help="print supported URL protocols", message=getMessageProtocols())
    parser.add_argument("-u", action="store_true", dest="umount", help="unmount")
    parser.add_argument("path", action="store", metavar="file | URL | alias", help= \
                        "file - path to local file\n" + \
                        "URL - remote source to be mounted\n" + \
                        "alias - alias specified in config file")
    parser.add_argument("-o", action="store", dest="options", nargs=1, metavar="opt[,opt...]", help="(u)mount options")
    args = parser.parse_args()
    

    if args.umount:
        if args.path == "all":
            for file in os.listdir(config["main"]["MainPath"]):
                path = os.path.join(config["main"]["MainPath"], file)
                if os.path.ismount(path):
                    umount(path, args.options)
        else:
            umount(args.path, args.options)
        cleanAll()
    else:
        cleanAll()
        if args.path in config["aliases"]:
            args = parser.parse_args(config["aliases"][args.path].split())
        mount = Mount(args.path, args.options)
