#! /bin/bash

# convert any video files in current directory to mp3

# exit on error
set -e

# extended globbing
shopt -s extglob
shopt -s nullglob

videos=*(*.flv|*.mp4|*.avi|*.mkv)

for file in $videos; do
    outputname="${file%.*}.mp3"

    ffmpeg -i "$file" -vn -acodec libmp3lame -ar 44100 -ab 128k -ac 2 -f mp3 "$outputname"

    if [[ $? -eq 0 ]]; then
        rm -f -- "$file"
    else
        rm -f -- "$outputname"
    fi
done
