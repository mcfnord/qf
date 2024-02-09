#!/bin/bash

# Read lines from standard input
while read -r line; do
    # Check if the line contains 'ACTIVE'
    if [[ "$line" == *"ACTIVE"* ]]; then
        /home/pi/.local/bin/kasa --host 192.168.1.128 --port 9999 --type plug on
    else
        /home/pi/.local/bin/kasa --host 192.168.1.128 --port 9999 --type plug off
    fi
done
