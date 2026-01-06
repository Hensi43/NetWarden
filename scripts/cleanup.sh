#!/bin/bash
echo "Cleaning up network throttling rules..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # MacOS
    echo "Flushing dummynet pipes..."
    sudo dnctl -f flush
    echo "Flushing PF anchor..."
    sudo pfctl -a com.antigravity.throttler -F all
else
    # Linux
    INTERFACE=$(grep "interface:" configs/policy.yaml | awk '{print $2}' | tr -d '"')
    if [ -z "$INTERFACE" ]; then INTERFACE="eth0"; fi
    
    echo "Resetting tc qdisc on $INTERFACE..."
    sudo tc qdisc del dev $INTERFACE root 2>/dev/null || true
fi

echo "Cleanup done."
