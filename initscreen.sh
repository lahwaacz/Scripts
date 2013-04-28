#! /bin/bash

hdmi=$(cat /sys/class/drm/card0-HDMI-A-1/status)
vga=$(cat /sys/class/drm/card0-VGA-1/status)

echo "initscreen.sh: hdmi $hdmi; vga $vga"

if [[ $hdmi == "connected" ]]; then
    # hdmi only
    xrandr --nograb --output LVDS --off --output HDMI-0 --auto --primary
    # both
#    xrandr --nograb --output LVDS --auto --output HDMI-0 --auto --primary --left-of LVDS
elif [[ $vga == "connected" ]]; then
    xrandr --nograb --output VGA-0 --auto --output LVDS --mode 1024x768 --primary
    # TODO:  look at --scale argument
else
    xrandr --nograb --output LVDS --auto --primary --output HDMI-0 --off
fi
