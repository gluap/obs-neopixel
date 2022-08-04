#!/bin/bash

if bluetoothctl info 9C:9C:1F:E9:FB:52 | grep "Connected: yes"; then
   echo "Disconnect"
   bluetoothctl disconnect 9C:9C:1F:E9:FB:52
fi

echo "Start bluetooth and neopixel"

sleep 3
cd $(dirname "$0")
python3 obs-neo.py
