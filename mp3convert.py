#! /usr/bin/env python

import sys
import os
import argparse
from multiprocessing import cpu_count
import threading
from time import sleep
import re
import shutil

# depends on python-scandir-git <https://aur.archlinux.org/packages/python-scandir-git>
import scandir

from pythonscripts.tempfiles import TempFiles
from pythonscripts.subprocess_extensions import getstatusoutput
from pythonscripts.ffparser import FFprobeParser


audio_types = ("mp3", "aac", "ac3", "mp2", "wma", "wav", "mka", "m4a", "ogg", "oga", "flac")
audio_file_regex = re.compile("^(?P<dirname>/(.*/)*)(?P<filename>.*(?P<extension>\.(" + "|".join(audio_types) + ")))$")
ffmpeg_command = "/usr/bin/ffmpeg -i %(input)s -acodec libmp3lame -ar 44100 -ab %(bitrate)dk -ac 2 -f mp3 -map_metadata 0 -y %(output)s"


class GettingBitrateError(Exception):
    def __init__(self, fname):
        self.message = "Couldn't get bitrate from file " + fname


class ConversionError(Exception):
    def __init__(self, fname, status, output):
        self.message = "Error while converting file " + fname + "\nffmpeg exited with status " + str(status) + "\n" + output


def get_bitrate(filename):
    parser = FFprobeParser(filename)
    bitrate = parser.get("audio", "bit_rate")
    del parser
    if bitrate is None:
        raise GettingBitrateError(filename)
    else:
        return bitrate // 1000


def convert(filename, output_extension, bitrate, delete_after=False):
    tmpfile = tmp.getTempFileName()
    command = ffmpeg_command % {"input": re.escape(filename), "bitrate": bitrate, "output": re.escape(tmpfile)}
    status, output = getstatusoutput(command)
    if status > 0:
        tmp.remove(tmpfile)
        raise ConversionError(filename, status, output)
    else:
        if delete_after:
            os.remove(filename)
        shutil.move(tmpfile, os.path.splitext(filename)[0] + output_extension)
        tmp.remove(tmpfile)


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


class Main():
    def __init__(self, args):
        self.countAudioFiles = 0
        self.countHigherBitrate = 0
        self.countDifferentFormat = 0
        self.countErrors = 0
        self.countNonAudioFiles = 0

        self.dry_run = args.dry_run
        self.bitrate = args.bitrate
        self.verbose = args.verbose
        self.recursive = args.recursive
        self.deleteAfter = args.delete_after
        self.outputExtension = "." + args.output_extension
        self.paths = args.path

        try:
            self.threads = cpu_count()
        except NotImplementedError:
            print("Unable to determine number of CPU cores, assuming one.")
            self.threads = 1

        self.killed = threading.Event()
        self.threadsFinished = 0
        self.queue = LockedIterator(self.queue_generator())

    def print_stats(self):
        print()
        print("-----------collected statistics-----------")
        print("All audio files (without errors):   % 6d" % self.countAudioFiles)
        print("Converted files:                    % 6d" % (self.countDifferentFormat + self.countHigherBitrate))
        print("    - different format:             % 6d" % self.countDifferentFormat)
        print("    - %3s but higher bitrate:       % 6d" % (self.outputExtension[1:], self.countHigherBitrate))
        print("Errors:                             % 6d" % self.countErrors)
        print("Non-audio files:                    % 6d" % self.countNonAudioFiles)
        print("------------------------------------------")

    def check(self, path):
        match = re.match(audio_file_regex, path)

        if not match:
            self.countNonAudioFiles += 1
            return False

        filename = match.group("filename")
        ext = match.group("extension")

        self.countAudioFiles += 1
        if ext != self.outputExtension:
            self.countDifferentFormat += 1
            return True

        bitrate = get_bitrate(path)
        if self.verbose > 0:
            sys.stdout.write("% 3s kb/s: %s\n" % (bitrate, filename))
        if bitrate > self.bitrate:
            self.countHigherBitrate += 1
            return True
        return False

    def run(self):
        for i in range(self.threads):
            t = threading.Thread(target=self.worker, args=(i + 1,))
            t.start()

        try:
            while self.threadsFinished < self.threads:
                sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            self.killed.set()

        self.print_stats()

    def worker(self, id):
        try:
            while not self.killed.is_set():
                i = next(self.queue)
                i = os.path.abspath(i)

                try:
                    # check bitrate/filetype etc., skip if conversion not necessary
                    if not self.check(i) or self.dry_run:
                        continue
                    convert(i, self.outputExtension, self.bitrate, self.deleteAfter)
                except ConversionError as e:
                    msg = "ERROR: failed to convert file '%s'\n" % i
                    if self.verbose > 0:
                        msg += e.message + "\n"
                    sys.stdout.write(msg)
                    self.countErrors += 1
                except GettingBitrateError as e:
                    msg = "ERROR: failed to get bitrate from file '%s'" % i
                    if self.verbose > 0:
                        msg += e.message + "\n"
                    sys.stdout.write(msg)
                    self.countErrors += 1
                else:
                    sys.stdout.write("Thread % 2d: %s\n" % (id, i))

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
            for entry in scandir.scandir(root):
                if entry.isdir():
                    dirs.append(entry.name)
                elif entry.isfile():
                    files.append(entry.name)

            # first yield found files, then recurse into subdirs
            for f in files:
                yield os.path.join(root, f)
            if self.recursive:
                for d in dirs:  # recurse into subdir
                    for f in walk(os.path.join(root, d)):
                        yield f

        for path in self.paths:
            if os.path.isdir(path):
                for f in walk(path):
                    yield f
            else:
                yield path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert all audio files in given folder (recursively) to specified bitrate, skip if bitrate is less or equal")
    parser.add_argument("path", action="store", nargs="+", help="path to file(s) to convert - filename or directory")
    parser.add_argument("-r", "--recursive", action="store_true", help="browse folders recursively")
    parser.add_argument("--dry-run", action="store_true", help="don't convert, only print stats")
    parser.add_argument("-b", "--bitrate", action="store", type=int, metavar="BITRATE", default="128", help="set bitrate - in kb/s, default=128")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="set verbosity level")
    parser.add_argument("--delete-after", action="store_true", help="delete old files after conversion")
    parser.add_argument("--output-extension", choices=audio_types, type=str, default="mp3", help="set output extension")

    args = parser.parse_args()

    tmp = TempFiles()
    main = Main(args)
    main.run()
