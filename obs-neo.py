import sys
import asyncio
import platform
import struct
from threading import Thread

## Neopixel
import time
import board
import neopixel
from PIL import Image, ImageFont, ImageDraw

from collections import deque
from statistics import median

# OBS Bluetooth
from bleak import BleakClient, BleakScanner

# setup GPIO
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

OBS_MAC = "40:91:51:9B:6E:22"
HANDLEBAR_OFFSET_UUID = "1FE7FAF9-CE63-4236-0004-000000000004"


BUTTON = 16
ARRANGEMENT =  "8x32" #"32x8"

handlebar_left = 30;

GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
last_button = GPIO.input(BUTTON)

##############################
# Prepare Neopixel
##############################

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 256

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1, auto_write=False, pixel_order=ORDER)

display_on = True

#
# Blutooth scanner config
#

timeout_seconds = 20
obs_address = None

i=0
last = deque(maxlen=3)

def notification_handler(sender, data):
    global display_on,i,handlebar_left


    """Simple notification handler which prints the data received."""
    t,lraw,r=struct.unpack("Ihh",data)

    last.append(lraw)
    l=median(last)
    l-=handlebar_left
    print(f"sensortime: {t}, Left distance {l}, right distance {r}")
    if l == -1-handlebar_left:
       show_text_on_display("___CM", (255,255,255)) # white
    elif l < 0:
       show_text_on_display("XXXXX", (255,0,0),0)
    elif l < 100:
       show_text_on_display(" " + str(l) + "CM", (255,0,0), l * 32 / 200) # red
    elif l < 150:
       show_text_on_display(str(l) + "CM", (255,255,0), l * 32 / 200) # yellow
    else:
       show_text_on_display(str(l) + "CM", (0,128,0), l * 32 / 200)  # green

def show_text_on_display(text, fill, length = None):

    image = Image.new('RGB', (32, 8), color="black")
    draw = ImageDraw.Draw(image)

    if display_on:
        font = ImageFont.load("6x9.pil")
        draw.text((1,-1), text, fill=fill, font=font)
        if length:
            draw.line([(0,7), (length,7)], fill, 1)

    for x in range(0, 32):
        for y in range(0, 8):
            if ARRANGEMENT == "8x32":
                i = x * 8
                if x % 2 == 0:
                    i += 7 - y
                else:
                    i += y
            elif ARRANGEMENT == "32x8":
                i = y * 32
                if y % 2 == 1:
                    i += 31 - x
                else:
                    i += x
            pixels[255-i] = image.getpixel((x,y))
    pixels.show()

def read_button():
    global display_on

    while True:
        current_button = GPIO.input(BUTTON)

        if last_button and not current_button:
            print("BUTTON pressed")
            display_on = not display_on
            time.sleep(1)

        current_button = last_button
        time.sleep(0.2)

async def main(address, char_uuid):
    # read input
    t = Thread(target=read_button)
    t.daemon = True
    t.start()

    await connect(address, char_uuid)

bt_connected = False

async def connect(address, char_uuid):
    global bt_connected, handlebar_left

    def disconnected_callback(client):
        global bt_connected
        print("DISCONNECTED");
        bt_connected = False

    async with BleakClient(address, disconnected_callback=disconnected_callback) as client:
        global handlebar_left
        print(f"Connected: {client.is_connected}")
        await client.start_notify(char_uuid, notification_handler)
        handlebar = await client.read_gatt_char(HANDLEBAR_OFFSET_UUID)
        handlebar_left, trash = struct.unpack("hh", handlebar)
        print(f"handlebar_left: {handlebar_left}")
        bt_connected = True
        while True:
            if not bt_connected:
                break
            await asyncio.sleep(0.5)

class MyScanner:
    def __init__(self):
        self._scanner = BleakScanner()
        self._scanner.register_detection_callback(self.detection_callback)
        self.scanning = asyncio.Event()

    def detection_callback(self, device, advertisement_data):
        global obs_address
        if device.name.startswith("OpenBikeSensor"):
            print(device)
            obs_address = device.address
            self.scanning.clear()

    async def run(self):
        global obs_address
        print("Scan for devices")
        show_text_on_display("OBS...", (255,255,255))   # white
        obs_address = None
        await self._scanner.start()
        self.scanning.set()
        end_time = loop.time() + timeout_seconds
        while self.scanning.is_set():
            if loop.time() > end_time:
                self.scanning.clear()
                print('Scan has timed out so we terminate')
            await asyncio.sleep(0.1)
        await self._scanner.stop()
        if obs_address == None:
            raise Exception('No OBS found')

my_scanner = MyScanner()
loop = asyncio.get_event_loop()

def run():
    loop.run_until_complete(my_scanner.run())

    CHARACTERISTIC_UUID = "1FE7FAF9-CE63-4236-0004-000000000002"
    ADDRESS = (
        obs_address
#        if platform.system() != "Darwin"
#        else "B9EA5233-37EF-4DD6-87A8-2A875E821C46"
    )

    asyncio.run(
        main(ADDRESS, CHARACTERISTIC_UUID)
    )

while True:
    try:
        run()
    except Exception as e:
        print(str(e));
        print("ERROR. Retry");
