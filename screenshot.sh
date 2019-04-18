#!/bin/sh

filename="$HOME/Bbox/shared/screenshot-%Y-%m-%d@%H:%M:%S.png"

screenshot() {
    case $1 in
    full)
        if [[ "$SWAYSOCK" != "" ]]; then
            grim $(date +"$filename")
        else
            scrot -m "$filename"
        fi
        notify-send "Taken screenshot:" $(date +$(basename $filename))
        ;;
    select)
        if [[ "$SWAYSOCK" != "" ]]; then
            local geometry=$(slurp 2>/dev/null)
            if [[ "$geometry" == "" ]]; then
                return
            fi
            grim -g "$geometry" $(date +"$filename")
        else
            scrot -s $filename
        fi
        notify-send "Taken screenshot:" $(date +$(basename $filename))
        ;;
    *)
        ;;
    esac;
}

screenshot $1
