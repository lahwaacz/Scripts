#! /usr/bin/env python2

import sys 
import os
import glob
import argparse
import subprocess

import mutagen
from mutagen.id3 import ID3, TXXX 

from pythonscripts.logger import Logger

class Main:
    def __init__(self, logger, options):
        self.log = logger
        self.log.filename = None
        self.force = options.force
        self.force_album = options.force_album
        self.force_track = options.force_track
        self.files = options.files
        self.raw_lines = []
        self.data_files = []
        self.data_album = {}

    def run(self):
        # check if all files have ReplayGain tags; mp3gain runs very long
        if not self.force and self.all_files_have_replaygain_tags():
            self.log.critical("All files already have ReplayGain tags, no action taken.", 0)
        self.run_mp3gain()
        self.update_tags()

    def all_files_have_replaygain_tags(self):
        for fname in self.files:
            # open id3 tag
            try: 
                id3 = ID3(fname) 
            except mutagen.id3.error: 
                return False

            # update tag
            tags = set([tag.desc.lower() for tag in id3.getall("TXXX") if tag.desc.lower().startswith("replaygain_")])
            return tags == set(["replaygain_track_gain", "replaygain_album_gain", "replaygain_track_peak", "replaygain_album_peak"])

    def run_mp3gain(self):
        self.log.debug("running mp3gain on all files")
        cmd = ["mp3gain","-q", "-o", "-s", "s"] + self.files
        try:
            raw_data = subprocess.check_output(cmd, universal_newlines=True)
            self.raw_lines = raw_data.splitlines()
        except subprocess.CalledProcessError as exc:
            code = exc.returncode
            msg = "mp3gain returned error status: " + str(code) + "\n"
            msg += "-----------mp3gain output dump-----------\n"
            msg += exc.output
            msg += "\n-----------------------------------------\n"
            self.log.critical(msg, code)

    def update_tags(self):
        self.log.debug("parsing mp3gain output")
        album_parts = self.raw_lines[-1].strip().split("\t")

        # just in case
        if album_parts[0] != '"Album"':
            self.log.critical("unable to parse mp3gain output")

        a_gain = float(album_parts[2])              # album gain
        a_peak = float(album_parts[3]) / 32768.0    # album peak
        
        del self.raw_lines[0]   # header
        del self.raw_lines[-1]  # album summary
        for line in self.raw_lines:
            parts = line.strip().split("\t")
            fname = parts[0]    # filename

            self.log.filename = fname
            self.log.debug("begin processing file") 

            t_gain = float(parts[2])                # track gain
            t_peak = float(parts[3]) / 32768.0      # track peak

            # set t_gain, t_peak, a_gain, a_peak depending on options
            if self.force_album:
                t_gain = a_gain
                t_peak = a_peak
            elif self.force_track:
                a_gain = t_gain
                a_peak = t_peak

            # open id3 tag
            try: 
                id3 = ID3(fname) 
            except mutagen.id3.error: 
                self.log.info("no ID3 tag found, creating one") 
                id3 = ID3() 

            # update tag
            modified = False 
            modified += self.update_tag(id3, "REPLAYGAIN_TRACK_GAIN", "%.2f dB" % t_gain)
            modified += self.update_tag(id3, "REPLAYGAIN_ALBUM_GAIN", "%.2f dB" % a_gain)
            modified += self.update_tag(id3, "REPLAYGAIN_TRACK_PEAK", "%.6f" % t_peak)
            modified += self.update_tag(id3, "REPLAYGAIN_ALBUM_PEAK", "%.6f" % a_peak)

            # save tag
            if modified: 
                self.log.debug("saving modified ID3 tag") 
                id3.save(fname) 

            self.log.debug("done processing file") 
            self.log.filename = None 

    def update_tag(self, id3, name, value):
        if not self.force and ("TXXX:%s" % name) in id3: 
            self.log.info("ID3 '%s' tag already exists, skpping tag" % name) 
            return False 
        id3.add(TXXX(encoding=1, desc=name, text=value)) 
        self.log.info("added ID3 '%s' tag with value '%s'" % (name, value)) 
        return True 


def main(prog_name, options): 
    logger = Logger(options.log_level, prog_name) 
    logger.debug("Selected mp3 files:")
    logger.debug("\n".join(sorted(options.files)))
    main = Main(logger, options) 
    main.run()


def expand_filename(path):
    path = os.path.expanduser(os.path.normpath(path))

    # stupid escape of special characters for glob
    pattern = ""
    for char in path:
        if char in "[] ?*":
            pattern += "[%s]" % char
        else:
            pattern += char

    if os.path.isdir(path):
        pattern += "/*.mp3"
    files = [f for f in glob.glob(pattern) if os.path.splitext(f)[1] == ".mp3" ]

    if not files:
        raise argparse.ArgumentTypeError("no mp3 files: '%s'" % path)
    return files
 

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Write correct ReplayGain tags into mp3 files; uses mp3gain internally") 
 
    # log level options
    log = parser.add_mutually_exclusive_group()
    log.add_argument("-q", "--quiet", dest="log_level", 
                        action="store_const", const=0, default=1, 
                        help="do not output error messages") 
    log.add_argument("-v", "--verbose", dest="log_level", 
                        action="store_const", const=3, 
                        help="output warnings and informational messages") 
    log.add_argument("-d", "--debug", dest="log_level", 
                        action="store_const", const=4, 
                        help="output debug messages") 
 
    parser.add_argument("--force", action="store_true",
                        help="force overwriting of existing ID3v2 ReplayGain tags") 
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--force-album", action="store_true",
                        help="write replaygain_album_{gain,peak} values into replaygain_track_{gain,peak} tags")
    group.add_argument("--force-track", action="store_true",
                        help="write replaygain_track_{gain,peak} values into replaygain_album_{gain,peak} tags")

    parser.add_argument("files", nargs="+", metavar="FILE | FOLDER | PATTERN", type=expand_filename,
                        help="path to mp3 file(s), globbing using the 'glob' python module supported")

    args = parser.parse_args()  # parse arguments
    args.files = [j for i in args.files for j in i]     # 'join' nested lists

    try: 
        main(sys.argv[0], args) 
    except KeyboardInterrupt: 
        pass 
