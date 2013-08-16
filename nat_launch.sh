#!/bin/bash

# Original author: Xyne
# http://xyne.archlinux.ca/notes/network/dhcp_with_dns.html

function print_usage() {
    echo "usage: $0 <WAN interface> <subnet interface> <up|down>"
}

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root." >&2
    exit 1
fi

if [[ -z $3 ]]; then
    print_usage
    exit 1
else
    wan_nic="$1"
    subnet_nic="$2"
    action="$3"
fi


mask=/24
subnet_ip=192.168.1.0$mask
server_ip=192.168.1.23$mask
iptables=/usr/bin/idemptables
dhcpd_conf=/etc/dhcpd.conf
dhcpd_lease=/run/dhcpd.lease
dhcpd_pid=/run/dhcpd.pid

source nat_launch_subnet.sh

launch_subnet "$action"
