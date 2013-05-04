#! /bin/bash

# toggle touchpad status

off=$(synclient -l | grep TouchpadOff | awk -F '= ' '{ print $2 }')

if [[ "$off" == "0" ]]; then
    synclient TouchpadOff=1
else
    synclient TouchpadOff=0
fi
