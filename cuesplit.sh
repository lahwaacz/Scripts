#!/bin/sh

# original source code from:
# http://bbs.archlinux.org/viewtopic.php?id=75774

# frontend for:            cuetools, shntool, mp3splt
# optional dependencies:    flac, mac, wavpack, ttaenc
# v1.3 sen

# exit on error
set -e

SDIR=`pwd`

if [ "$1" = "" ]
  then
    DIR=$SDIR
else
    case $1 in
        -h | --help )
            echo "Usage: cuesplit [Path]"
            echo "       The default path is the current directory."
            exit
            ;;
        * )
        DIR=$1
    esac
fi

echo -e "\

Directory: $DIR
________________________________________
"
cd "$DIR"
TYPE=`ls -t1`

case $TYPE in
    *.ape*)
        mkdir -p split
        shnsplit -d split -f *.cue -o "flac flac -V --best -o %f -" *.ape -t "%n %p - %t"
        rm -f split/00*pregap*
        cuetag.sh *.cue split/*.flac
        exit
        ;;

    *.flac*)
        mkdir -p split
        shnsplit -d split -f *.cue -o "flac flac -V --best -o %f -" *.flac -t "%n %p - %t"
        rm -f split/00*pregap*
        cuetag.sh *.cue split/*.flac
        exit
        ;;

    *.mp3*)
        mp3splt -no "@n @p - @t (split)" -c *.cue *.mp3
        cuetag.sh *.cue *split\).mp3
        exit
        ;;

    *.ogg*)
        mp3splt -no "@n @p - @t (split)" -c *.cue *.ogg
        cuetag.sh *.cue *split\).ogg
        exit
        ;;

    *.tta*)
        mkdir -p split
        shnsplit -d split -f *.cue -o "flac flac -V --best -o %f -" *.tta -t "%n %p - %t"
        rm -f split/00*pregap*
        cuetag.sh *.cue split/*.flac
        exit
        ;;

    *.wv*)
        mkdir -p split
        shnsplit -d split -f *.cue -o "flac flac -V --best -o %f -" *.wv -t "%n %p - %t"
        rm -f split/00*pregap*
        cuetag.sh *.cue split/*.flac
        exit
        ;;

    *.wav*)
        mkdir -p split
        shnsplit -d split -f *.cue -o "flac flac -V --best -o %f -" *.wav -t "%n %p - %t"
        rm -f split/00*pregap*
        cuetag.sh *.cue split/*.flac
        exit
        ;;

    * )
    echo "Error: Found no files to split!"
    echo "       --> APE, FLAC, MP3, OGG, TTA, WV, WAV"
esac
exit
