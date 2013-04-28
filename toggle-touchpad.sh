#! /bin/bash

# toggle touchpad status

if [ $(synclient -l | grep TouchpadOff | awk -F '= ' '{ print $2 }') -eq 0 ]; then
    synclient TouchpadOff=1
else
    synclient TouchpadOff=0
fi
