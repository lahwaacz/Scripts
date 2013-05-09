#! /usr/bin/env python

import sys
import os
import argparse
from multiprocessing import cpu_count
import threading
from time import sleep
import re
import shutil

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


class Main():
    def __init__(self, args):
        self.countAudioFiles = 0
        self.countHigherBitrate = 0
        self.countDifferentFormat = 0
        self.countErrors = 0
        self.countNonAudioFiles = 0
        
        self.bitrate = args.bitrate
        self.verbose = args.verbose
        self.recursive = args.recursive
        self.deleteAfter = args.delete_after
        self.outputExtension = "." + args.output_extension
        
        self.filesToConvert = []
        
        try:
            self.threads = cpu_count()
        except NotImplementedError:
            print("Unable to determine number of CPU cores, assuming one.")
            self.threads = 1

        self.killed = False
        self.threadsFinished = 0
        self.lock = threading.Lock()
        
    def analyze(self, args):
        for filename in args:
            if os.path.isdir(filename):
                self.browse(filename)
            else:
                self.check(filename)
        
        print("All audio files (without errors):", self.countAudioFiles)
        print("All files to convert:            ", self.countDifferentFormat + self.countHigherBitrate)
        print("    - different format:          ", self.countDifferentFormat)
        print("    - " + self.outputExtension[1:] + " but higher bitrate:    ", self.countHigherBitrate)
        print("Errors:                          ", self.countErrors)
        print("Non-audio files:                 ", self.countNonAudioFiles)
    
    def browse(self, path):
        path = os.path.abspath(path)
        filenames = os.listdir(path)
        for filename in filenames:
            filename = os.path.join(path, filename)
            if os.path.isdir(filename):
                if self.recursive:
                    self.browse(filename)
            else:
                self.check(filename)
            
    def check(self, filename):
        try:
            path = os.path.abspath(filename)
            match = re.match(audio_file_regex, path)

            if not match:
                self.countNonAudioFiles += 1
                return

            filename = match.group("filename")
            ext = match.group("extension")
            
            self.countAudioFiles += 1
            if ext != self.outputExtension:
                self.countDifferentFormat += 1
                self.filesToConvert.append(path)
                return

            bitrate = get_bitrate(path)
            if self.verbose > 0:
                print(str(bitrate) + "kb/s: " + filename)
            if bitrate > self.bitrate:
                self.countHigherBitrate += 1
                self.filesToConvert.append(path)
        
        except GettingBitrateError as e:
            self.countErrors += 1
            if self.verbose > 0:
                print(e.message)
            else:
                print("ERROR while getting bitrate from file ", filename)
            
    def convert(self, filename):
        tmpfile = tmp.getTempFileName()
        command = ffmpeg_command % {"input": re.escape(filename), "bitrate": self.bitrate, "output": re.escape(tmpfile)}
        status, output = getstatusoutput(command)
        if status > 0:
            tmp.remove(tmpfile)
            raise ConversionError(filename, status, output)
        else:
            if self.deleteAfter:
                os.remove(filename)
            shutil.move(tmpfile, os.path.splitext(filename)[0] + self.outputExtension)
            tmp.remove(tmpfile)
            
    def worker(self, id):
        while not self.killed:
            try:
                self.lock.acquire()
                fname = self.filesToConvert.pop(0)
                self.lock.release()
                self.convert(fname)
            except IndexError:
                self.lock.release()
                break
            except ConversionError as e:
                if self.verbose > 0:
                    print(e.message)
                else:
                    print("ERROR: converting file", fname, "failed")
            else:
                print("Thread " + str(id) + ": " + fname)
        self.threadsFinished += 1
            
    def convert_all(self):
        self.filesToConvert.sort()
        
        for i in range(self.threads):
            v = threading.Thread(target=self.worker, args=(i + 1,))
            v.start()
        
        try:
            while self.threadsFinished < self.threads:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.killed = True
            print("Interrupt signal received, exiting...")
        else:
            print("Conversion finished.")
        finally:
            sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert all audio files in given folder (recursively) to specified bitrate")
    parser.add_argument("path", action="store", nargs="+", help="path to file(s) to convert - filename or directory")
    parser.add_argument("-r", "--recursive", action="store_true", help="browse folders recursively")
    parser.add_argument("-c", "--convert", action="store_true", help="convert files to specified bitrate, skip if bitrate is less or equal")
    parser.add_argument("-b", "--bitrate", action="store", type=int, metavar="BITRATE", default="128", help="set bitrate - in kb/s, default=128")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="set verbosity level")
    parser.add_argument("--delete-after", action="store_true", help="delete old files after conversion")
    parser.add_argument("--output-extension", choices=audio_types, type=str, default="mp3", help="set output extension")

    args = parser.parse_args()
    
    tmp = TempFiles()
    main = Main(args)
    main.analyze(args.path)
    if args.convert:
        main.convert_all()
