#! /bin/bash

# exit on error
set -e

hdmi=$(cat /sys/class/drm/card0-HDMI-A-1/status)
vga=$(cat /sys/class/drm/card0-VGA-1/status)

echo "initscreen.sh: hdmi $hdmi; vga $vga"

if [[ $hdmi == "connected" ]]; then
    # hdmi only
    # NOTE: i3 fails if no active output is detected, so we have to first enable second output and then disable the first
#    xrandr --nograb --output HDMI-0 --auto --primary
#    xrandr --nograb --output LVDS --off
    # both
    xrandr --nograb --output LVDS --auto --output HDMI-0 --auto --primary --right-of LVDS
elif [[ $vga == "connected" ]]; then
    xrandr --nograb --output VGA-0 --auto --output LVDS --mode 1024x768 --primary
    # TODO:  look at --scale argument
else
    xrandr --nograb --output LVDS --auto --primary --output HDMI-0 --off
fi
