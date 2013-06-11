#!/bin/bash

# volume control (up/down/mute/unmute/toggle) + notification

# duration in ms
duration=1500

notify () {
    # get volume level
    percent=$(ponymix get-volume)

    # check if muted, set title
    ponymix is-muted && title="Volume muted" || title="Volume"

    # create fancy bar
    f=$((percent/10))
    e=$((10-f))
    fchars='◼◼◼◼◼◼◼◼◼◼'
    echars='◻◻◻◻◻◻◻◻◻◻'
    bar="${fchars:0:f}${echars:0:e} $percent%"

    notify-send --app-name=VolumeNotification --expire-time="$duration" --urgency=low "$title" "$bar"
}

# redirect stdout of this script to /dev/null
exec > /dev/null

case "$1" in
    up)
        ponymix increase 5%
        ponymix unmute
        ;;
    down)
        ponymix decrease 5%
        ponymix unmute
        ;;
    mute)
        ponymix mute
        ;;
    unmute)
        ponymix unmute
        ;;
    toggle)
        ponymix toggle
        ;;
esac

notify
