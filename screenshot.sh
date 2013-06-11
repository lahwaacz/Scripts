#!/bin/sh

filename="/home/lahwaacz/Dropbox/shared/screenshot-%Y-%m-%d@%H:%M:%S.png"

screenshot() {
    case $1 in
    full)
        scrot -m $filename
        notify-send "Taken screenshot:" $(date +$(basename $filename))
        ;;
    window)
        sleep 1
        scrot -s $filename
        notify-send "Taken screenshot:" $(date +$(basename $filename))
        ;;
    *)
        ;;
    esac;
}

screenshot $1
