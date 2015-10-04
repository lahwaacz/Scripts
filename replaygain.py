#! /usr/bin/env python3

import sys 
import os
import argparse
import subprocess
from multiprocessing import cpu_count
import threading
from time import sleep

import taglib

from pythonscripts.logger import Logger

class ReplayGain:
    """ Will consider all files to belong to one album.
    """

    def __init__(self, logger, options, files):
        # logger
        self.log = logger
        self.log.filename = None

        # internals
        self.raw_lines = []
        self.data_files = []
        self.data_album = {}

        # options
        self.force = options.force
        self.force_album = options.force_album
        self.force_track = options.force_track
        self.files = files

    def run(self):
        # check if all files have ReplayGain tags; mp3gain runs very long
        if not (self.force or self.force_album or self.force_track) and self.all_files_have_replaygain_tags():
            self.log.error("All files already have ReplayGain tags, no action taken.")
            return
        if self.run_mp3gain():
            self.update_tags()

    def all_files_have_replaygain_tags(self):
        """ Quick analysis to determine if input files contain replaygain_* tags.
        """
        for fname in self.files:
            # open id3 tag
            f = taglib.File(fname) 

            tags = set([tag.lower() for tag in f.tags.keys() if tag.lower().startswith("replaygain_")])
            return tags == set(["replaygain_track_gain", "replaygain_album_gain", "replaygain_track_peak", "replaygain_album_peak"])

    def run_mp3gain(self):
        """ Compute values for replaygain_* tags.
        """
        self.log.debug("running mp3gain on specified files")
        cmd = ["mp3gain", "-q", "-o", "-s", "s"] + self.files
        ret = True
        try:
            raw_data = subprocess.check_output(cmd, universal_newlines=True)
            self.raw_lines = raw_data.splitlines()
        except subprocess.CalledProcessError as exc:
            code = exc.returncode
            msg = "mp3gain returned error status: " + str(code) + "\n"
            msg += "-----------mp3gain output dump-----------\n"
            msg += exc.output
            msg += "\n-----------------------------------------\n"
            self.log.error(msg)
            ret = False
        except Exception as e:
            print(e)
            ret = False
            raise
        finally:
            return ret

    def update_tags(self):
        """ Add computed replaygain_* tags into all files.
        """
        self.log.debug("parsing mp3gain output")
        album_parts = self.raw_lines[-1].strip().split("\t")

        # just in case
        if album_parts[0] != '"Album"':
            self.log.error("unable to parse mp3gain output")
            return

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
            f = taglib.File(fname)

            # update tag
            f.tags["REPLAYGAIN_TRACK_GAIN"] = "%.2f dB" % t_gain
            f.tags["REPLAYGAIN_ALBUM_GAIN"] = "%.2f dB" % a_gain
            f.tags["REPLAYGAIN_TRACK_PEAK"] = "%.6f" % t_peak
            f.tags["REPLAYGAIN_ALBUM_PEAK"] = "%.6f" % a_peak

            # save tag
            self.log.debug("saving modified ID3 tag") 
            f.save() 

            self.log.debug("done processing file") 
            self.log.filename = None 


# thread-safe iterating over generators
class LockedIterator(object):
    def __init__(self, it):
        self.lock = threading.Lock()
        self.it = it.__iter__()

    def __iter__(self):
        return self

    def __next__(self):
        self.lock.acquire()
        try:
            return next(self.it)
        finally:
            self.lock.release()


class Main:
    """ Will parse input pattern and create ReplayGain object on every directory found.
    """

    def __init__(self, logger, options):
        self.logger = logger
        self.options = options
        self.recursive = options.recursive
        self.paths = options.files
        del options.recursive   # don't want to pass it to ReplayGain object
        del options.files   # don't want to pass it to ReplayGain object

        try:
            self.threads = cpu_count()
        except NotImplementedError:
            print("Unable to determine number of CPU cores, assuming one.")
            self.threads = 1

        self.killed = threading.Event()
        self.threadsFinished = 0
        self.queue = LockedIterator(self.queue_generator())

    def run(self):
        for i in range(self.threads):
            t = threading.Thread(target=self.worker, args=(i + 1,))
            t.start()

        try:
            while self.threadsFinished < self.threads:
                sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            self.killed.set()

    def worker(self, id):
        try:
            while not self.killed.is_set():
                i = next(self.queue)
                i = sorted(list(i))

                # skip dirs not containing any mp3 file
                if len(i) == 0:
                    continue

                # write info
                sys.stdout.write("Thread %d:\n  %s\n\n" % (id, "\n  ".join(i)))

                try:
                    # create ReplayGain object, pass files and run
                    rg = ReplayGain(self.logger, self.options, i)
                    rg.run()
                except Exception as e:
                    print(e)
                    raise
        except StopIteration:
            pass
        finally:
            self.threadsFinished += 1

    def queue_generator(self):
        """ For each directory in self.files returns generator returning full paths to mp3 files in that folder.
            If self.files contains file paths instead of directory, it's returned as [file].
        """

        def walk(root):
            dirs = []
            files = []
            for entry in os.scandir(root):
                if entry.is_dir():
                    dirs.append(entry.name)
                elif entry.is_file() and entry.name.endswith(".mp3"):
                    files.append(entry.name)

            # first yield found files, then recurse into subdirs
            if files:
                yield (os.path.join(root, x) for x in files)
            if self.recursive:
                for d in dirs:  # recurse into subdir
                    for x in walk(os.path.join(root, d)):
                        yield x

        for path in self.paths:
            if os.path.isdir(path):
                for x in walk(path):
                    yield x
            else:
                yield [path]

def main(prog_name, options): 
    logger = Logger(options.log_level, prog_name) 
    logger.debug("Selected mp3 files:")
    logger.debug("\n".join(sorted(options.files)))
    main = Main(logger, options) 
    main.run()

def argparse_path_handler(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("invalid path: '%s'" % path)
    if os.path.isfile(path) and not path.endswith(".mp3"):
        raise argparse.ArgumentTypeError("not a mp3 file: '%s'" % path)
    return os.path.abspath(path)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Write correct ReplayGain tags into mp3 files; uses mp3gain internally") 
 
    # log level options
    log = parser.add_mutually_exclusive_group()
    log.add_argument("-q", "--quiet", dest="log_level", action="store_const", const=0, default=1, help="do not output error messages") 
    log.add_argument("-v", "--verbose", dest="log_level", action="store_const", const=3, help="output warnings and informational messages") 
    log.add_argument("-d", "--debug", dest="log_level", action="store_const", const=4, help="output debug messages") 
 
    parser.add_argument("-r", "--recursive", action="store_true", help="when path to directory is specified, browse it recursively (albums still respected)")
    parser.add_argument("--force", action="store_true", help="force overwriting of existing ID3v2 ReplayGain tags") 
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--force-album", action="store_true", help="write replaygain_album_{gain,peak} values into replaygain_track_{gain,peak} tags")
    group.add_argument("--force-track", action="store_true", help="write replaygain_track_{gain,peak} values into replaygain_album_{gain,peak} tags")

    parser.add_argument("files", nargs="+", metavar="FILE | FOLDER", type=argparse_path_handler, help="path to mp3 file(s) or directory(ies)")

    args = parser.parse_args()
    main(sys.argv[0], args) 
