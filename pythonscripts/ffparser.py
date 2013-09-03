#!/usr/bin/env python

import json
import re
import subprocess
from pprint import pprint


ffprobe = "ffprobe -v quiet -print_format json -show_format -show_streams "


class FFprobeParser:
    def __init__(self, path):
        self.data = json.loads(subprocess.check_output(ffprobe + re.escape(path), shell=True, universal_newlines=True))

        self.format = self.data["format"]
        self.audio = None
        self.video = None
        for stream in self.data["streams"]:
            if self.audio is None and stream["codec_type"] == "audio":
                self.audio = stream
            if self.video is None and stream["codec_type"] == "video":
                self.video = stream

    def _get(self, option, attribute):
        return getattr(self, option)[attribute]

    def _getBitrate(self, option):
        if option == "audio":
            try:
                return int(self._get("audio", "bit_rate"))
            except:
                return int(self._getBitrate("format")) - int(self._getBitrate("video"))
        elif option == "video":
            try:
                return int(self._get("video", "bit_rate"))
            except:
                return int(self._getBitrate("format")) - int(self._getBitrate("audio"))
        elif option == "format":
            try:
                return int(self._get("format", "bit_rate"))
            except:
                return None

    def get(self, option, attribute):
        """ 'option' is one of "audio", "video", "format"
            'attribute' is the json attribute to query
        """
        if attribute == "bit_rate":
            return self._getBitrate(option)
        else:
            try:
                return self._get(option, attribute)
            except:
                return None

    def pprint(self, option):
        """ 'option' is one of "audio", "video", "format",
            otherwise 'self.data' is printed
        """
        pprint(getattr(self, option, self.data))

