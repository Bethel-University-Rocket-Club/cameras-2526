#!/bin/bash
IFACE=wwu1u3i5
WDM=/dev/cdc-wdm0

# Wait for interface to appear
for i in $(seq 1 30); do
    ip link show $IFACE > /dev/null 2>&1 && break
    sleep 1
done

# Set raw_ip mode
ip link set $IFACE down
echo Y > /sys/class/net/$IFACE/qmi/raw_ip
ip link set $IFACE up

# Clear stale qmi-network state
rm -f /tmp/qmi-network-state-cdc-wdm0

# Start network
qmi-network $WDM start

# Wait for bearer to come up
sleep 3

# Get current IPv6 settings and apply
SETTINGS=$(qmicli -d $WDM --wds-get-current-settings --device-open-proxy)

IPV6=$(echo "$SETTINGS" | grep "IPv6 address" | awk '{print $3}')
GW=$(echo "$SETTINGS" | grep "IPv6 gateway address:" | grep -oP '[0-9a-f:]+(?=\/)')

ip addr flush dev $IFACE
ip addr add $IPV6 dev $IFACE
ip route add default via $GW dev $IFACE
