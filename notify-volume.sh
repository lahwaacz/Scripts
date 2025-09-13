#!/bin/bash

# volume control (up/down/mute/unmute/toggle) + notification

# duration in ms
duration=1500

notify () {
    # get volume level
    percent=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -n 1)

    # check if muted, set title
    if [[ $(pactl get-sink-mute @DEFAULT_SINK@) == "Mute: yes" ]]; then
        title="Volume muted"
    else
        title="Volume"
    fi

    # create fancy bar
    f=$((percent/10))
    e=$((10-f))
    fchars='◼◼◼◼◼◼◼◼◼◼'
    echars='◻◻◻◻◻◻◻◻◻◻'
    bar="${fchars:0:f}${echars:0:e} $percent%"

    notify-send --app-name=VolumeNotification --category=device --expire-time="$duration" --urgency=low --transient "$title" "$bar"
}

# redirect stdout of this script to /dev/null
exec > /dev/null

case "$1" in
    up)
        pactl set-sink-volume @DEFAULT_SINK@ +5%
        pactl set-sink-mute @DEFAULT_SINK@ 0
        ;;
    down)
        pactl set-sink-volume @DEFAULT_SINK@ -5%
        pactl set-sink-mute @DEFAULT_SINK@ 0
        ;;
    mute)
        pactl set-sink-mute @DEFAULT_SINK@ 1
        ;;
    unmute)
        pactl set-sink-mute @DEFAULT_SINK@ 0
        ;;
    toggle)
        pactl set-sink-mute @DEFAULT_SINK@ toggle
        ;;
esac

notify
