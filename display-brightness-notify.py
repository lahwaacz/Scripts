#!/usr/bin/env python

from subprocess import check_call

def get_lcd_level():
    f = open("/sys/class/backlight/acpi_video0/brightness", "r")
    level = f.read()
    f.close()
    return int(level)

def notify(title, content, icon, duration=5):
    check_call("twmnc --id 89 --title '%s' --content '%s' --icon '%s' --duration %s" % (title, content, icon, duration*1000), shell=True)

percent = get_lcd_level() * 100 // 15

if percent <= 5:
    icon = "notification-display-brightness-off"
elif percent <= 30:
    icon = "notification-display-brightness-low"
elif percent <= 60:
    icon = "notification-display-brightness-medium"
elif percent <= 80:
    icon = "notification-display-brightness-high"
else:
    icon = "notification-display-brightness-full"
title = "LCD brightness:"
content = str(percent) + "%"
time = 5

notify(title, content, icon, time)
