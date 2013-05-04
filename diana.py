#! /usr/bin/env python

# simple RPC interface to aria2c
# based on: https://github.com/baskerville/diana

# TODO: --save-session doesn't save items added by addUri method

from pythonscripts import *

import urllib.request, json, base64
from urllib.error import URLError, HTTPError
import sys, os
from getopt import getopt
from collections import defaultdict
import subprocess
import argparse

PORT = 6868
EXIT_CODES = {
    "1":"unknown",
    "2":"timeout",
    "3":"resource not found",
    "4":"resources not found",
    "5":"download speed too slow",
    "6":"network problem",
    "7":"unfinished downloads",
    "8":"resume not supported",
    "9":"not enough disk space",
    "10":"piece length differ",
    "11":"was downloading the same file",
    "12":"was downloading the same info hash",
    "13":"file already existed",
    "14":"renaming failed",
    "15":"could not open existing file",
    "16":"could not create new or truncate existing",
    "17":"file I/O",
    "18":"could not create directory",
    "19":"name resolution failed",
    "20":"could not parse metalink",
    "21":"FTP command failed",
    "22":"HTTP response header was bad or unexpected",
    "23":"too many redirections",
    "24":"HTTP authorization failed",
    "25":"could not parse bencoded file",
    "26":"torrent was corrupted or missing informations",
    "27":"bad magnet URI",
    "28":"bad/unrecognized option or unexpected option argument",
    "29":"the remote server was unable to handle the request",
    "30":"could not parse JSON-RPC request"
 }


def _call_func(func, params=[]):
    jsonreq = json.dumps({"id":"foo", "method":"aria2.%s" % func, "params":params}).encode("utf-8")
    try:
        c = urllib.request.urlopen("http://localhost:"+str(PORT)+"/jsonrpc", jsonreq)
    except IOError as err:
        if type(err) is URLError:
            return err.reason.errno, None
        elif type(err) is HTTPError:
            return err.code, None
    data = c.read().decode("utf-8")
    response = json.loads(data)
    return 0, response

def call_func(func, params=[]):
    code, response = _call_func(func, params)
    if response is None:
        print("server replied: %s" % code, file=sys.stderr)
    else:
        return response
    sys.exit(1)

def apply_func_on_gids(fn, gids):
    for g in gids:
        code, response = _call_func(fn, [str(g)])
        if response is None:
            print("failed on %s" % g)

def get_active():
    return call_func("tellActive")

def get_waiting():
    return call_func("tellWaiting", [0, 666])

def get_stopped():
    return call_func("tellStopped", [0, 666])

def is_daemon_running():
    code, response = _call_func("getGlobalStat")
    return not code


def show_queue(kind="all"):
    width = getTerminalSize()[0]
    namewidth = max(width - 96, 25)

    line_format = (
        '{gid:<16} {status:<8} {name:<'+str(namewidth)+'}  {percent:>7}  '
        '{completed_length:>8}  {total_length:>8}  {down_speed:>8}  {up_speed:>8}  '
        '{seeders:>4}/{connections:<4}  {eta:<6}'
    )
    header = {"gid":"gid", "status":"status", "name":"name", "percent":"percent", "completed_length":"complete", "total_length":"total", "down_speed":"down spd", "up_speed":"up spd", "seeders":"seed", "connections":"conn", "eta":"eta"}
    print(colorize("white", line_format.format_map(header).strip()))

    downloads = []
    if kind in ("all", "active"):
        downloads.extend(get_active()["result"])
    if kind in ("all", "waiting"):
        downloads.extend(get_waiting()["result"])
    if kind in ("all", "stopped"):
        downloads.extend(get_stopped()["result"])

    for d in downloads:
        completed_length = float(d["completedLength"])
        total_length = float(d["totalLength"])
        remaining_length = total_length - completed_length
        download_speed = float(d["downloadSpeed"])
        percent = 0;
        if (total_length > 0):
            percent = 100 * completed_length / total_length

        line_items = defaultdict(lambda: "n/a")

        line_items["gid"] = d["gid"]
        line_items["status"] = d["status"]
        try:
            line_items["name"] = d["bittorrent"]["info"]["name"]
        except:
            try:
                line_items["name"] = d["files"][0]["path"]
            except:
                pass
        if len(line_items["name"]) > namewidth:
            line_items["name"] = line_items["name"][:namewidth - 3] + "..."
        line_items["percent"] = "%.1f %%" % percent
        line_items["completed_length"] = sizeof_fmt(completed_length, "short")
        line_items["total_length"] = sizeof_fmt(total_length, "short")
        line_items["down_speed"] = sizeof_fmt(download_speed, "short") + "/s"
        line_items["up_speed"] = sizeof_fmt(float(d["uploadSpeed"]), "short") + "/s"
        if "numSeeders" in d:
            line_items["seeders"] = d["numSeeders"]
        line_items["connections"] = d["connections"]
        if download_speed > 0:
            line_items["eta"] = formatTime(remaining_length // download_speed)

        color = getColor(line_items["status"], download_speed)
        print(colorize(color, line_format.format_map(line_items).strip()))
        if kind == "all":
            show_errors(None)


def daemon_start(args):
    cmd = "aria2c -D --quiet --enable-rpc --rpc-listen-port="+str(PORT)+" --rpc-save-upload-metadata=true --save-session=~/.aria2/diana-session"
    if os.path.exists("~/.aria2/diana-session"):
        cmd += " --input-file=~/.aria2/diana-session"
    cmd += " -j 2 -l ~/.aria2/diana-log"
    subprocess.call(cmd, shell=True)

def daemon_kill(args):
    call_func("shutdown")

def show_all(args):
    show_queue()

def show_active(args):
    show_queue("active")

def show_paused(args):
    show_queue("waiting")

def show_stopped(args):
    show_queue("stopped")

def show_errors(args):
    stopped = get_stopped()
    for r in stopped["result"]:
        if r["status"] == "error":
            errorCode = r["errorCode"]
            error = EXIT_CODES[errorCode]
            print(colorize("red", "%3s %s (error %s)" % (r["gid"], error, errorCode)))

def show_stats(args):
    stats = call_func("getGlobalStat")["result"]
    for key in sorted(stats.keys()):
        value = stats[key]
        print("%24s: " % colorize("black", key), end="")
        if "Speed" in key:
            print("%s/s" % sizeof_fmt(float(value), "short"))
        else:
            print(value)

def sleep(args):
    call_func("pauseAll")

def wake(args):
    call_func("unpauseAll")

def purge(args):
    call_func("purgeDownloadResult")

def clean(args):
    for d in get_active()["result"]:
        completed_length = int(d["completedLength"])
        total_length = int(d["totalLength"])
        if completed_length >= total_length:
            apply_func_on_gids("remove", [d["gid"]])

def add_items(args):
    args.options=dict(",".join(args.options))
    for item in args.item:
        if os.path.isfile(item):
            item_content = base64.b64encode(open(item, "rb").read()).decode("utf-8")
            if item.endswith(".torrent"):
                code, response = _call_func("addTorrent", [item_content, [], args.options])
            elif item.endswith(".meta4") or item.endswith(".metalink"):
                code, response = _call_func("addMetalink", [item_content, args.options])
        else:
            code, response = _call_func("addUri", [[item], args.options])

        if code != 0:
            print("failed on %s" % item)
        else:
            print(response["result"])

def remove_items(args):
    apply_func_on_gids("remove", args.gid)

def forcerm(args):
    apply_func_on_gids("forceRemove", args.gid)

def pause(args):
    apply_func_on_gids("pause", args.gid)

def resume(args):
    apply_func_on_gids("unpause", args.gid)
    
def move(args):
    call_func("changePosition", [args.gid, args.position, "POS_SET"])

def show_files(args):
    for g in args.gid:
        if len(gids) > 1:
            print(colorize("magenta", g + ": "))
        files = call_func("getFiles", [g])["result"]
        for f in files:
            total_length = float(f["length"])
            completed_length = float(f["completedLength"])
            percent = 0

            if (total_length > 0):
                percent = 100 * completed_length / total_length

            percent = "%.1f" % percent
            if f["selected"] == "true":
                mark = "[X]"
            else:
                mark = "[ ]"

            output_line = "%s %2s %5s%% %s" % (mark, f["index"], percent, f["path"])

            if completed_length >= total_length:
                output_line = colorize("green", output_line)

            print(output_line)

def change_global_option(args):
    call_func("changeGlobalOption", [{args.option: args.value}])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple script controlling aria2 in daemon mode.")
    subparsers = parser.add_subparsers()
    parser_start = subparsers.add_parser("start", help="Start the daemon.")
    parser_start.set_defaults(func=daemon_start)
    parser_kill = subparsers.add_parser("kill", help="Kill the daemon.")
    parser_kill.set_defaults(func=daemon_kill)
    parser_active = subparsers.add_parser("active", help="Show the list of active downloads.")
    parser_active.set_defaults(func=show_active)
    parser_paused = subparsers.add_parser("paused", help="Show the list of paused downloads.")
    parser_paused.set_defaults(func=show_paused)
    parser_stopped = subparsers.add_parser("stopped", help="Show the list of stopped downloads.")
    parser_stopped.set_defaults(func=show_stopped)
    parser_errors = subparsers.add_parser("errors", help="Show the list of encountered errors.")
    parser_errors.set_defaults(func=show_errors)
    parser_stats = subparsers.add_parser("stats", help="Show download bandwidth statistics.")
    parser_stats.set_defaults(func=show_stats)
    parser_sleep = subparsers.add_parser("sleep", help="Pause all the active downloads.")
    parser_sleep.set_defaults(func=sleep)
    parser_wake = subparsers.add_parser("wake", help="Resume all the paused downloads.")
    parser_wake.set_defaults(func=wake)
    parser_purge = subparsers.add_parser("purge", help="Clear the list of stopped downloads and errors.")
    parser_purge.set_defaults(func=purge)
    parser_clean = subparsers.add_parser("clean", help="Stop seeding completed downloads.")
    parser_clean.set_defaults(func=clean)

    parser_add = subparsers.add_parser("add", help="Download the given items (local or remote URLs to torrents, etc.).")
    parser_add.add_argument("item", action="store", nargs="+", help="Local or remote URI to torrents, metalinks, etc.")
    parser_add.add_argument("-o", dest="options", nargs="+", default=[], metavar="OPTION", help="additional options passed to aria2, `key=val` pairs expected")
    parser_add.set_defaults(func=add_items)
    parser_remove = subparsers.add_parser("remove", help="Remove the downloads corresponding to the given GIDs.")
    parser_remove.add_argument("gid", action="store", nargs="+", metavar="GID")
    parser_remove.set_defaults(func=remove_items)
    parser_forcerm = subparsers.add_parser("forcerm", help="Forcibly remove the downloads corresponding to the given GIDs.")
    parser_forcerm.add_argument("gid", action="store", nargs="+", metavar="GID")
    parser_forcerm.set_defaults(func=forcerm)
    parser_pause = subparsers.add_parser("pause", help="Pause the downloads corresponding to the given GIDs.")
    parser_pause.add_argument("gid", action="store", nargs="+", metavar="GID")
    parser_pause.set_defaults(func=pause)
    parser_resume = subparsers.add_parser("resume", help="Resume the downloads corresponding to the given GIDs.")
    parser_resume.add_argument("gid", action="store", nargs="+", metavar="GID")
    parser_resume.set_defaults(func=resume)
    parser_files = subparsers.add_parser("files", help="Show the files owned by the downloads corresponding to the given GIDs.")
    parser_files.add_argument("gid", action="store", nargs="+", metavar="GID")
    parser_files.set_defaults(func=show_files)
    parser_move = subparsers.add_parser("move", help="Move the item corresponding to the given GID in queue to specified POSITION. Use '+' or '-' to move relatively to current position.")
    parser_move.add_argument("gid", action="store", metavar="GID")
    parser_move.add_argument("position", action="store")
    parser_move.set_defaults(func=move)
    parser_set = subparsers.add_parser("set", help="Change the global option of the daemon. See `man aria2c` for more information.")
    parser_set.add_argument("option", action="store", help="Name of the option.")
    parser_set.add_argument("value", action="store", help="Value of the option.")
    parser_set.set_defaults(func=change_global_option)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        setattr(args, "func", show_all)

    daemon_running = is_daemon_running()
    if not daemon_running and args.func != daemon_start:
        print("daemon is not running", file=sys.stderr)
        sys.exit(1)
    if daemon_running and args.func == daemon_start:
        print("daemon is already running", file=sys.stderr)
        sys.exit(1)

    args.func(args)
