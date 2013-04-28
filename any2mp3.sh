#!/bin/bash
# convert any video files in current directory to mp3

# exit on error
set -e

IFS=$'\012'
for file in $(find . -maxdepth 1 -mindepth 1 -iname "*.flv" -o -iname "*.mp4" -o -iname "*.avi" -o -iname "*.mkv"); do
	outputname="${file%.*}.mp3"

	ffmpeg -i "$file" -vn -acodec libmp3lame -ar 44100 -ab 128k -ac 2 -f mp3 "$outputname" && rm -f -- "${file}" || rm -f -- "${outputname}"
done
