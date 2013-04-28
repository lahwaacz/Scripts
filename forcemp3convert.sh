#! /bin/bash

set -e

for file in "$@"; do
    ffmpeg -i "$file" -acodec libmp3lame -ar 44100 -ab 128k -ac 2 -f mp3 -map_metadata 0 -y /tmp/tmpname.mp3
    mv /tmp/tmpname.mp3 "${file%\.*}.mp3"
done
