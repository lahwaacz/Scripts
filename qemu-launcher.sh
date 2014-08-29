#! /usr/bin/bash

# Author: Jakub Klinkovský (Lahwaacz)
# https://github.com/lahwaacz

function print_usage() {
    echo "usage: $0 <VM name>"
}

## Generate name of TAP interface to create
function get_tap_name() {
    for (( i=0; i<$tap_limit; i++ )); do
        local name="tap$i"
        if [[ ! -d "/sys/class/net/$name" ]]; then
            echo "$name"
            break
        fi
    done
}

# do not run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script is not supposed to be run as root." >&2
    exit 1
fi

# parse command line arguments
if [[ -z $1 ]]; then
    print_usage
    exit 1
else
    vm_name="$1"
fi


sudo_args=("-Ap" "Enter your root password (QEMU launcher script)")
username=$(whoami)
tap_limit=10            # maximum number of TAP interfaces created by this script
tap_nic=$(get_tap_name)
br_nic="qemu-br0"       # bridge interface name (will be created)
wan_nic="wlan0"         # WAN interface name (for NAT)


case "$vm_name" in
    btrfs)
        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" up

        qemu-system-x86_64 \
            -name "$vm_name" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga qxl -spice port=5931,disable-ticketing \
            -drive file="/home/lahwaacz/virtual_machines/archlinux-btrfs.raw",if=virtio,cache=none -boot once=c \
            -net nic,model=virtio,macaddr=$(qemu-mac-hasher.py "$vm_name") -net tap,ifname="$tap_nic",script=no,downscript=no \
            -usbdevice tablet

        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" down
    ;;
    virtarch)
        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" up

        qemu-system-x86_64 \
            -name "$vm_name" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga qxl -spice port=5931,disable-ticketing \
            -drive file="/home/lahwaacz/virtual_machines/archlinux.raw",if=virtio,cache=none -boot once=c \
            -net nic,model=virtio,macaddr=$(qemu-mac-hasher.py "$vm_name") -net tap,ifname="$tap_nic",script=no,downscript=no \
            -usbdevice tablet

        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" down
    ;;
    winxp)
        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" up

        qemu-system-i386 \
            -name "$vm_name" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga qxl -spice port=5930,disable-ticketing \
            -drive file="/home/lahwaacz/virtual_machines/winxp.raw",if=virtio,cache=none -boot order=c \
            -net nic,model=virtio,macaddr=$(qemu-mac-hasher.py "$vm_name") -net tap,ifname="$tap_nic",script=no,downscript=no \
            -usbdevice tablet \
            -soundhw ac97 \
            -localtime

        sudo "${sudo_args[@]}" qemu-tap-helper.sh "$username" "$tap_nic" "$br_nic" "$wan_nic" down
    ;;
    liveiso)
        if [[ -z "$2" ]]; then
            echo "You must specify the ISO file as a second argument." >&2
            exit 1
        fi

        qemu-system-x86_64 \
            -name "$vm_name" \
            -monitor stdio \
            -enable-kvm -smp 2 -cpu host -m 1024 \
            -vga std \
            -drive file="$2",if=virtio,media=cdrom -boot once=d \
            -net nic -net user \
            -usbdevice tablet
    ;;
    *)
        echo "Unknown VM name specified: $vm_name" >&2
        exit 1
    ;;
esac


### frequently/previously used options:

## user-mode networking
# -net nic,model=virtio -net user

## user-mode networking with redirect (localhost:2222 -> 10.0.2.15:22)
# -net nic,model=virtio -net user -redir tcp:2222:10.0.2.15:22
