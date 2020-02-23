#!/bin/sh
# Toggle touchpad status
# Using libinput and xinput
# 0 input disables in and anything else enables it

toggleto(){ # If input is 0 disable it, otherwise enable it
    [ "$1" = "0" ] && xinput disable "$device" || xinput enable "$device" ;}

# Use xinput list and do a search for touchpads. Then get the first one and get its name.
device="$(xinput list | grep -P '(?<= )[\w\s:]*(?i)touchpad(?-i).*?(?=\s*id)' -o | head -n1)"
# If there is an input switch to that, otherwise just toggle
[ -n "$1" ] && toggleto "$1" || toggleto "$([ "$(xinput list-props "$device" | grep -P ".*Device Enabled.*\K.(?=$)" -o)" = "1" ] && echo 0 || echo 1)"
