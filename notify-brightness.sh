#! /bin/bash

# LCD brightness notification (level changed by ACPI, no action required)

id=90
duration=5

level=$(cat "/sys/class/backlight/acpi_video0/brightness")
percent=$(( $level * 100 / 15 ))
title="LCD brightness:"

twmnc --id "$id" --title "$title" --content "$percent%" --duration "$duration"
