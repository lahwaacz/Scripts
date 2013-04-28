#!/usr/bin/env python

import sys
import os
import optparse
from multiprocessing import cpu_count
import threading
from time import sleep
import re
import shutil

from pythonscripts.tempfiles import TempFiles
from pythonscripts.subprocess_extensions import getstatusoutput
from pythonscripts.ffparser import FFprobeParser
    

AUDIO_TYPES = (".mp3", ".aac", ".ac3", ".mp2", ".wma", ".wav", ".mka", ".m4a", ".ogg", ".oga", ".flac")


class GettingBitrateError(Exception):
    def __init__(self, fname):
        self.message = "Couldn't get bitrate from file " + fname
    
class ExtensionError(Exception):
    pass

class ConversionError(Exception):
    def __init__(self, fname, status, output):
        self.message = "Error while converting file " + fname + "\nffmpeg exited with status " + str(status) + "\n" + output
    

def print_formats(option, opt, value, parser):
    print("Supported audio formats:")
    print(", ".join(AUDIO_TYPES))
    sys.exit(0)

def get_bitrate(filename):
    parser = FFprobeParser(filename)
    bitrate = parser.get("audio", "bit_rate")
    del parser
    if bitrate is None:
        raise GettingBitrateError(filename)
    else:
        return bitrate // 1000


class Main():
    def __init__(self):
        self.countAudioFiles = 0
        self.countHigherBitrate = 0
        self.countDifferentFormat = 0
        self.countErrors = 0
        self.countNonAudioFiles = 0
        
        self.bitrate = 128
        self.verbose = False
        self.recursive = False
        self.deleteAfter = False
        self.outputExtension = ".mp3"
        
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
        print("    - " + self.outputExtension + " but higher bitrate:   ", self.countHigherBitrate)
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
            filename = os.path.abspath(filename)
            ext = os.path.splitext(filename)[1]
            if ext not in AUDIO_TYPES:
                if ext == ".old":
                    new = os.path.splitext(filename)[0]
                    ext = os.path.splitext(new)[1]
                    if os.path.splitext(new)[1] in AUDIO_TYPES:
                        if os.path.exists(new):
                            os.remove(new)
                        os.rename(filename, new)
                        filename = new
                else:
                    raise ExtensionError
            
            self.countAudioFiles += 1
            if ext != self.outputExtension:
                self.countDifferentFormat += 1
                self.filesToConvert.append(filename)
                return

            bitrate = get_bitrate(filename)
            if self.verbose:
                print(str(bitrate) + "kb/s: " + os.path.split(filename)[1])
            if bitrate > self.bitrate:
                self.countHigherBitrate += 1
                self.filesToConvert.append(filename)
        
        except ExtensionError:
            self.countNonAudioFiles += 1
                    
        except GettingBitrateError as e:
            self.countErrors += 1
            if self.verbose:
                print(e.message)
            else:
                print("ERROR while getting bitrate from file ", filename)
            
    def convert(self, filename):
        tmpfile = tmp.getTempFileName()
        command = "/usr/bin/ffmpeg " + " -i " + re.escape(filename) + " -acodec libmp3lame -ar 44100 -ab " + \
                str(self.bitrate) + "k -ac 2 -f mp3 -map_metadata 0 -y " + re.escape(tmpfile)
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
                if self.verbose:
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
    usage = "%prog [option] [option argument] filename OR foldername"
    description = "Mp3Convert converts all audio files in given folder (recursively) to desired bitrate."
    parser = optparse.OptionParser(usage=usage, description=description)
    parser.add_option("-f", "--formats", action="callback", callback=print_formats, \
                      help="print supported file types and exit")
    parser.add_option("-r", action="store_true", dest="recursive", default=False, \
                      help="browse folders recursively")
    parser.add_option("-c", "--convert", action="store_true", dest="convert", \
                      default=False, help="convert files to desired bitrate, skip if bitrate is less or equal")
    parser.add_option("-b", "--bitrate", action="store", type="int", dest="bitrate", \
                      metavar="BITRATE", default="128", \
                      help="set desired bitrate - in kb/s, default=128")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", \
                      default=False, help="be verbose - print converter's output")
    parser.add_option("--delete-after", action="store_true", dest="deleteAfter", \
                      default=False, help="delete old files after conversion")
    parser.add_option("--output-extension", action="store", type="str", dest="outputExtension", \
                      default="mp3", help="set output extension")
    options, args = parser.parse_args()
    
    if args != []:
        tmp = TempFiles()
        main = Main()
        main.verbose = options.verbose
        main.bitrate = options.bitrate
        main.recursive = options.recursive
        main.deleteAfter = options.deleteAfter
        main.outputExtension = "." + options.outputExtension.replace(".", "")
        if main.outputExtension not in AUDIO_TYPES:
            print("ERROR: invalid output extension " + main.outputExtension)
            sys.exit(1)
        main.analyze(args)
        if options.convert:
            main.convert_all()
    else:
        parser.print_help()
