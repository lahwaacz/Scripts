#! /usr/bin/bash

# Author: Jakub Klinkovský (Lahwaacz)
# https://github.com/lahwaacz

## Check if a string represents a network interface
# $1: potential interface name
function is_interface() {
    [[ -d "/sys/class/net/$1" ]]
}

## Generate name of TAP interface to create
function get_tap_name() {
    for (( i=0; i<$TAP_LIMIT; i++ )); do
        local name="tap$i"
        if ! is_interface "$name"; then
            echo "$name"
            break
        fi
    done
}

## Create new TAP interface
# $1: name of the interface to create
function create_tap() {
    if ! is_interface "$1"; then
        echo "Creating new TAP interface"
        sudo ip tuntap add "$1" mode tap user "$USER"
        sudo ip link set dev "$1" up
    fi
}

## Delete TAP interface
# $1: name of the interface to delete
function del_tap() {
    if is_interface "$1"; then
        echo "Deleting TAP interface '$1'"
        sudo ip link set dev "$1" down
        sudo ip tuntap del "$1" mode tap
    fi
}

## Check if the bridge has any interface
# $1: bridge interface name
function bridge_is_empty() {
    [[ $(ls "/sys/class/net/$1/brif" | wc -w) == "0" ]]
}

## Create bridge interface if it does not exist
# $1: bridge interface name
function create_br() {
    if is_interface "$1"; then
        if [[ ! -d "/sys/class/net/$1/brif" ]]; then
            echo "Interface '$1' already exists and is not a bridge"
            exit 1
        fi
    else
        echo "Creating bridge interface '$1'"
        sudo ip link add name "$1" type bridge
        sudo ip link set dev "$1" up

        # Xyne's excellent script to launch NAT
        echo "Starting NAT"
        sudo nat_launch.sh "$WAN_IFACE" "$1" up
    fi
}

## Delete bridge interface if it exists and has no interface
# $1: bridge interface name
function del_br() {
    if is_interface "$1" && bridge_is_empty "$1"; then
        echo "Stopping NAT"
        sudo nat_launch.sh "$WAN_IFACE" "$1" down

        echo "Deleting bridge interface '$1'"
        sudo ip link set dev "$1" down
        sudo ip link delete "$1" type bridge
    fi
}

## Add interface to the bridge
# $1: bridge interface name
# $2: name of the interface to add
function br_add_iface() {
    echo "Adding interface '$2' to bridge '$1'"
    sudo ip link set dev "$2" promisc on up
    sudo ip addr flush dev "$2" scope host &>/dev/null
    sudo ip addr flush dev "$2" scope site &>/dev/null
    sudo ip addr flush dev "$2" scope global &>/dev/null
    sudo ip link set dev "$2" master "$1"
}

## Remove interface from the bridge
# $1: bridge interface name
# $2: name of the interface to remove
function br_rm_iface() {
    echo "Removing interface '$2' from bridge '$1'"
    sudo ip link set "$2" promisc off down
    sudo ip link set dev "$2" nomaster
}

