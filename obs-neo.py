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

# OBS Bluetooth
from bleak import BleakClient

# setup GPIO
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

OBS_MAC = "9C:9C:1F:C4:A3:7E"
BUTTON = 16

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

##############################
# Prepare Bluetooth
##############################

# you can change these to match your device or override them from the command line
CHARACTERISTIC_UUID = "1FE7FAF9-CE63-4236-0004-000000000002"
ADDRESS = (
    OBS_MAC
    if platform.system() != "Darwin"
    else "B9EA5233-37EF-4DD6-87A8-2A875E821C46"
)

display_on = True

def notification_handler(sender, data):
    global display_on

    """Simple notification handler which prints the data received."""
    t,l,r=struct.unpack("Ihh",data)
    print(f"sensortime: {t}, Left distance {l}, right distance {r}")

    if l < 100:
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
            i = x * 8
            if x % 2 == 1:
                i += 7 - y
            else:
                i += y
            pixels[i] = image.getpixel((x,y))
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
        time.sleep(0.1)

async def main(address, char_uuid):
    # read input
    t = Thread(target=read_button)
    t.daemon = True
    t.start()

    await connect(address, char_uuid)

bt_connected = False

async def connect(address, char_uuid):
    global bt_connected

    show_text_on_display("OBS...", (255,255,255))   # white

    def disconnected_callback(client):
        global bt_connected
        print("DISCONNECTED");
        bt_connected = False

    async with BleakClient(address, disconnected_callback=disconnected_callback) as client:
        print(f"Connected: {client.is_connected}")
        await client.start_notify(char_uuid, notification_handler)
        bt_connected = True
        while True:
            if not bt_connected:
                break
            await asyncio.sleep(1)

def run():
    asyncio.run(
        main(
            sys.argv[1] if len(sys.argv) > 1 else ADDRESS,
            sys.argv[2] if len(sys.argv) > 2 else CHARACTERISTIC_UUID,
        )
    )

while True:
    try:
        run()
    except Exception as e:
        print(str(e));
        print("ERROR. Retry");
