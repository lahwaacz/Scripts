#! /bin/bash

# LCD brightness notification (level changed by ACPI, no action required)

# duration in ms
duration=1500

# get brightness level, set title
level=$(cat "/sys/class/backlight/intel_backlight/brightness")
max=$(cat "/sys/class/backlight/intel_backlight/max_brightness")
percent=$(( $level * 100 / $max ))
title="LCD brightness"

# create fancy bar
f=$((percent/10))
e=$((10-f))
fchars='◼◼◼◼◼◼◼◼◼◼'
echars='◻◻◻◻◻◻◻◻◻◻'
bar="${fchars:0:f}${echars:0:e} $percent%"

notify-send --app-name=VolumeNotification --expire-time="$duration" --urgency=low --transient "$title" "$bar"
