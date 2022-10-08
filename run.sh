#!/bin/bash

echo "Start bluetooth and neopixel"

sleep 3
cd $(dirname "$0")
python3 obs-neo.py
