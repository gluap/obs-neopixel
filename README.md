# LED-Matrix

## Dependencies

Raspberry Pi OS

```
sudo apt install python3-pip libopenjp2-7 libtiff5
sudo pip3 install pillow rpi_ws281x adafruit-circuitpython-neopixel bleak==0.14.3
```

**Hint**: Bleak 0.15 does not work!

Run with:

```
sudo python obs-neo.py
```

## Font

Font taken from https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/fonts and converted with Pillow (see https://stackoverflow.com/questions/48304078/python-pillow-and-font-conversion).
