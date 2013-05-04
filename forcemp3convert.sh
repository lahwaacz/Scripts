#! /bin/bash

# forcefully convert any file to mp3 (with fixed bitrate), preserving metadata (if possible)

set -e

for file in "$@"; do
    tmpfile="$(mktemp -u)-forcemp3convert.mp3"
    ffmpeg -i "$file" -acodec libmp3lame -ar 44100 -ab 128k -ac 2 -f mp3 -map_metadata 0 -y "$tmpfile"
    mv "$tmpfile" "${file%\.*}.mp3"
done
