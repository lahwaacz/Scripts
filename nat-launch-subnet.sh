#!/bin/bash


function print_launch_subnet_usage()
{
  echo "USAGE"
  echo "  $0 <up|down>"
  cat <<'CONFIG'

REQUIRED VARIABLES
  # The network interface card (NIC) that is connected to the internet or other
  # wide area network.
  wan_nic="wlan0"

  # The network interface card connected to the subnet.
  subnet_nic="eth0"

  # The subnet IP mask.
  mask=/24

  # The subnet IP range.
  subnet_ip=10.0.0.0$mask

  # The IP of the subnet NIC on the subnet.
  server_ip=10.0.0.100$mask

  # The IP tables binary to use.
  iptables=/usr/bin/idemptables

  # The dnsmasq arguments - PID and lease files to use.
  dnsmasq_pid=/tmp/dhcpd.pid
  dnsmasq_lease=/tmp/dhcpd.lease

  # The port of DNS service, see dnsmasq(8) for details. Specify "0" to disable DNS server.
  dnsmasq_port=53

  # The DHCP range, see dnsmasq(8) for details.
  dnsmasq_dhcp_range="192.168.1.100,192.168.1.200,12h"

OPTIONAL VARIABLES
  # Function or external scripts to run before before and after bringing the
  # subnet NIC up or down: pre_up, post_up, pre_down, post_down

  # pre_up as a function:
  # function pre_up()
  # {
  # }

  # pre_up as a script:
  # pre_up=/path/to/script

  # ip_forward=0
  # The value of /proc/sys/net/ipv4/ip_forward to restore when shutting down
  # the subnet.
CONFIG
}

function launch_subnet()
{
  set -e

  if [[ -z $1 ]]
  then
    print_launch_subnet_usage
    exit 1
  else
    action="$1"
  fi

  if [[ -z $wan_nic ]]
  then
    echo "wan_nic is undefined"
    exit 1
  fi

  if [[ -z $subnet_nic ]]
  then
    echo "subnet_nic is undefined"
    exit 1
  fi

  if [[ -z $mask ]]
  then
    echo "mask is undefined"
    exit 1
  fi

  if [[ -z $subnet_ip ]]
  then
    echo "subnet_ip is undefined"
    exit 1
  fi

  if [[ -z $server_ip ]]
  then
    echo "server_ip is undefined"
    exit 1
  fi

  if [[ -z $iptables ]]
  then
    echo "iptables is undefined"
    exit 1
  fi

  if [[ -z $dnsmasq_pid ]]
  then
    echo "dnsmasq_pid is undefined"
    exit 1
  fi

  if [[ -z $dnsmasq_lease ]]
  then
    echo "dnsmasq_lease is undefined"
    exit 1
  fi

  if [[ -z $dnsmasq_port ]]
  then
    echo "dnsmasq_port is undefined"
    exit 1
  fi

  if [[ -z $dnsmasq_dhcp_range ]]
  then
    echo "dnsmasq_dhcp_range is undefined"
    exit 1
  fi


  case "$action" in
    up)

      # Enable IP forwarding.
      echo 1 > /proc/sys/net/ipv4/ip_forward

      ## iptables rules are changed to fit my firewall config
      ## see http://xyne.archlinux.ca/notes/network/dhcp_with_dns.html for original rules

      # Open up DNS (53) and DHCP (67) ports on subnet_nic.
      "$iptables" -A nat-subnet -i "$subnet_nic" -s "$subnet_ip" -p tcp --dport 53 -j ACCEPT
      "$iptables" -A nat-subnet -i "$subnet_nic" -s "$subnet_ip" -p udp --dport 53 -j ACCEPT
      "$iptables" -A nat-subnet -i "$subnet_nic" -p udp --dport 67 -j ACCEPT

      # Reply to ICMP (ping) packets so clients can check their connections.
      "$iptables" -A nat-subnet -i "$subnet_nic" -p icmp --icmp-type echo-request -j ACCEPT
      #"$iptables" -A OUTPUT -i "$subnet_nic" -p icmp --icmp-type echo-reply -j ACCEPT

      # Allow postrouting to wan_nic (for e.g. internet access on the subnet).
      "$iptables" -t nat -A POSTROUTING -s "$subnet_ip" -o "$wan_nic" -j MASQUERADE

      # Enable forwarding from subnet_nic to wan_nic (and back via related and established connections).
      "$iptables" -A FORWARD -i "$subnet_nic" -s "$subnet_ip" -o "$wan_nic" -j ACCEPT
      "$iptables" -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

      # Bring down subnet_nic, configure it and bring it up again.
      if [[ ! -z $pre_up ]]
      then
        ip link set dev "$subnet_nic" down
        "$pre_up"
      fi
      ip link set dev "$subnet_nic" up
      if [[ ! -z $post_up ]]
      then
        "$post_up"
      fi

      # Set the static IP for subnet_nic.
      ip addr add "$server_ip" dev "$subnet_nic"

      # Ensure the lease file exists.
      mkdir -p -- "${dnsmasq_lease%/*}"
      [[ -f $dnsmasq_lease ]] || touch "$dnsmasq_lease"

      # Launch the DHCP server
      dnsmasq \
          --pid-file="$dnsmasq_pid" \
          --dhcp-leasefile="$dnsmasq_lease" \
          --port="$dnsmasq_port" \
          --interface="$subnet_nic" \
          --except-interface=lo \
          --bind-interfaces \
          --dhcp-range="$dnsmasq_dhcp_range" \
          --dhcp-authoritative \
          --dhcp-option=6,"${server_ip%/*}"
    ;;

    down)
      # Kill the DHCP server.
      if [[ -f $dnsmasq_pid ]]
      then
        kill $(cat "$dnsmasq_pid") && rm "$dnsmasq_pid" && echo "killed server"
      fi

      if [[ ! -z $pre_down ]]
      then
        "$pre_down"
      fi
      ip addr delete "$server_ip" dev "$subnet_nic"
      ip link set dev "$subnet_nic" down
      if [[ ! -z $post_down ]]
      then
        "$post_down"
      fi

      # Undo all of the changes above in reverse order.
      "$iptables" -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
      "$iptables" -D FORWARD -i "$subnet_nic" -s "$subnet_ip" -o "$wan_nic" -j ACCEPT
      "$iptables" -t nat -D POSTROUTING -s "$subnet_ip" -o "$wan_nic" -j MASQUERADE
      #"$iptables" -D OUTPUT -i "$subnet_nic" -p icmp --icmp-type echo-reply -j ACCEPT
      "$iptables" -D nat-subnet -i "$subnet_nic" -p icmp --icmp-type echo-request -j ACCEPT
      "$iptables" -D nat-subnet -i "$subnet_nic" -p udp --dport 67 -j ACCEPT
      "$iptables" -D nat-subnet -i "$subnet_nic" -s "$subnet_ip" -p udp --dport 53 -j ACCEPT
      "$iptables" -D nat-subnet -i "$subnet_nic" -s "$subnet_ip" -p tcp --dport 53 -j ACCEPT


      if [[ ! -z $ip_forward ]]
      then
        if [[ $ip_forward != $(cat /proc/sys/net/ipv4/ip_forward) ]]
        then
          echo $ip_forward > /proc/sys/net/ipv4/ip_forward
        fi
      else
        echo 0 > /proc/sys/net/ipv4/ip_forward
      fi
    ;;

    *)
      print_launch_subnet_usage
      exit 1
    ;;
  esac
}
