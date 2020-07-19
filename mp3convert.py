#! /usr/bin/env python3

import sys
import os
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
import shutil
import subprocess
import shlex

from pythonscripts.cpu import cores_count
from pythonscripts.tempfiles import TempFiles
from pythonscripts.ffparser import FFprobeParser


audio_types = ("mp3", "aac", "ac3", "mp2", "wma", "wav", "mka", "m4a", "ogg", "oga", "flac")
audio_file_regex = re.compile("^(?P<dirname>/(.*/)*)(?P<filename>.*(?P<extension>\.(" + "|".join(audio_types) + ")))$")
ffmpeg_command = "ffmpeg -i {input} -acodec libmp3lame -ar 44100 -ab {bitrate:d}k -ac 2 -f mp3 -map_metadata 0 -y {output}"


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
    command = ffmpeg_command.format(input=shlex.quote(filename), bitrate=bitrate, output=shlex.quote(tmpfile))
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        if delete_after:
            os.remove(filename)
        shutil.move(tmpfile, os.path.splitext(filename)[0] + output_extension)
        tmp.remove(tmpfile)
    except subprocess.CalledProcessError as e:
        tmp.remove(tmpfile)
        raise ConversionError(filename, e.returncode, e.output)


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

    async def run(self):
        # We could use the default single-threaded executor with basically the same performance
        # (because of Python's GIL), but the ThreadPoolExecutor allows to limit the maximum number
        # of workers and thus the maximum number of concurrent subprocesses.
        with ThreadPoolExecutor(max_workers=cores_count()) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, self.worker, path)
                for path in self.queue_generator()
            ]
            for result in await asyncio.gather(*tasks):
                pass

        self.print_stats()

    def worker(self, path):
        path = os.path.abspath(path)

        try:
            # check bitrate/filetype etc., skip if conversion not necessary
            if not self.check(path) or self.dry_run:
                return
            print("Converting: {}".format(path))
            convert(path, self.outputExtension, self.bitrate, self.deleteAfter)
        except ConversionError as e:
            msg = "ERROR: failed to convert file '{}'".format(path)
            if self.verbose > 0:
                msg += "\n" + e.message
            print(msg, file=sys.stderr)
            self.countErrors += 1
        except GettingBitrateError as e:
            msg = "ERROR: failed to get bitrate from file '{}'".format(path)
            if self.verbose > 0:
                msg += "\n" + e.message
            print(msg, file=sys.stderr)
            self.countErrors += 1
        else:
            print("Done: {}".format(path))

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
                elif entry.is_file():
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
    asyncio.run(main.run())
