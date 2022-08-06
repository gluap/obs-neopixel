#!/bin/bash

OBS_MAC="9C:9C:1F:C4:A3:7E"

if bluetoothctl info $OBS_MAC | grep "Connected: yes"; then
   echo "Disconnect"
   bluetoothctl disconnect $OBS_MAC
fi

echo "Start bluetooth and neopixel"

sleep 3
cd $(dirname "$0")
python3 obs-neo.py
