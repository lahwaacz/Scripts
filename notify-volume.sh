#!/bin/bash

# volume control (up/down/mute/unmute/toggle) + notification

id=91
duration=5

notify () {
    title="Volume set to"
    percent=$(ponymix get-volume)
    content="$percent%"

    ponymix is-muted
    if [[ $? -eq 0 ]]; then
        title="Volume muted"
        content=""
    fi

    twmnc --id "$id" --title "$title" --content "$content" --duration "$duration"
}

# redirect all output to /dev/null
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
