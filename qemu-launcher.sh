#! /usr/bin/bash

# Author: Jakub Klinkovský (Lahwaacz)
# https://github.com/lahwaacz

source qemu-launcher-functions.sh

# maximum number of TAP interfaces created by this script
TAP_LIMIT=10
# bridge interface name
BR_NAME="qemu-br0"
# WAN interface name (for NAT)
WAN_IFACE="wlan0"


case "$1" in
    virtarch)
        create_br "$BR_NAME"
        name=$(get_tap_name)
        create_tap "$name"
        br_add_iface "$BR_NAME" "$name"

        qemu-system-x86_64 \
            -name "virtarch" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga qxl -spice port=5931,disable-ticketing \
            -drive file="/home/lahwaacz/Virtual.Machines/archlinux.raw",if=virtio,cache=none -boot once=c \
            -net nic,model=virtio,macaddr=$(qemu-mac-hasher.py "virtarch") -net tap,ifname="$name",script=no,downscript=no \
            -usbdevice tablet

        br_rm_iface "$BR_NAME" "$name"
        del_tap "$name"
        del_br "$BR_NAME"
        ;;
    winxp)
        create_br "$BR_NAME"
        name=$(get_tap_name)
        create_tap "$name"
        br_add_iface "$BR_NAME" "$name"

        qemu-system-i386 \
            -name "winxp" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga qxl -spice port=5930,disable-ticketing \
            -drive file="/home/lahwaacz/Virtual.Machines/winxp.raw",if=virtio,cache=none -boot order=c \
            -net nic,model=virtio,macaddr=$(qemu-mac-hasher.py "winxp") -net tap,ifname="$name",script=no,downscript=no \
            -usbdevice tablet \
            -soundhw ac97 \
            -localtime

        br_rm_iface "$BR_NAME" "$name"
        del_tap "$name"
        del_br "$BR_NAME"
        ;;
    liveiso)
        if [[ -z "$2" ]]; then
            echo "Error: you must specify the ISO file as a second argument."
            exit 1
        fi

        qemu-system-x86_64 \
            -name "liveiso" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga std \
            -drive file="$2",if=virtio,media=cdrom -boot once=d \
            -net nic -net user \
            -usbdevice tablet
        ;;
    *)
        echo "No known VM name specified."
        exit 1
        ;;
esac


### frequently/previously used options:

## user-mode networking
# -net nic,model=virtio -net user

## user-mode networking with redirect (localhost:2222 -> 10.0.2.15:22)
# -net nic,model=virtio -net user -redir tcp:2222:10.0.2.15:22
