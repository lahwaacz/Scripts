#!/bin/bash
# convert any *.flv videos in current directory to mp4 (h264 video codec, mp3 audio codec)

# exit on error
set -e

IFS=$'\012'
for file in $(find . -maxdepth 1 -mindepth 1 -iname "*.flv"); do
	vbps=$(ffparser.py -v -g bit_rate $file)
	abps=$(ffparser.py -a -g bit_rate $file)
	outputname="${file%.*}.mp4"

	echo filename is $file
	echo video bitrate set to $vbps
	echo audio bitrate set to $abps

	ffmpeg -i "$file" -codec:v libx264 -x264opts bframes=2:subme=6:mixed-refs=0:weightb=0:ref=5:8x8dct:me=umh:direct=spatial:trellis=0:b-adapt=2 -b:v $vbps -codec:a libmp3lame -b:a $abps -f mp4 -n "$outputname" && rm -f -- "$file" || rm -f -- "$outputname"
done
