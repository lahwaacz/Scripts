#!/bin/bash

devices="$@"
devices=${devices:-/dev/sda}

for device in $devices; do
    cmd="smartctl -d ata -a $device | grep \"Temperature_Celsius\" | awk '{print \$10}'"

    if [[ $UID != 0 ]]; then
        echo "Running \`sudo $cmd\`"
        temp=$(eval "sudo $cmd")
    else
        echo "Running \`$cmd\`"
        temp=$(eval "$cmd")
    fi

    echo "Temperature of $device: $temp°C"
done
