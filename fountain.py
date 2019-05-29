#!/usr/bin/python3
# Fountain project
#
# xxxxxxxxxxxxxx


# interrupt-based GPIO example using LEDs and pushbuttons

import RPi.GPIO as GPIO
import time
import threading
import time
import board
import neopixel
import logging
import signal
import sys


from temperature import Temperature
from water_level import WaterLevel
from http_request import HttpServer

# Configure GPIO pins
motion_detect_pin = 17  # G17
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 2

display_auto_off_time_seconds = 5

display_off_timer = None

water_level = 0.0


def motionHandler(channel):
    global display_off_timer
    logging.info('In motionHandler')
    if display_off_timer is not None:
        display_off_timer.cancel()

    pixels.fill((255, 0, 0))
    # pixels.show()
    display_off_timer = threading.Timer(
        display_auto_off_time_seconds, turnOffDisplay)
    display_off_timer.daemon = True
    display_off_timer.start()


def turnOffDisplay():
    global display_off_timer
    logging.info('In turnOffDisplay')
    display_off_timer = None
    pixels.fill((0, 0, 0))


def signal_handler(signal, frame):
    logging.info('Shutdown...')
    GPIO.cleanup()
    httpd.server_close()
    httpd._BaseServer__shutdown_request = True
    # httpd.shutdown()
    # TODO: Perform cleanup code
    sys.tracebacklimit = 0
    sys.exit(0)



signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Docs: https://docs.python.org/3/library/logging.html
logging.basicConfig(level=logging.NOTSET,
                    format='%(asctime)-15s %(threadName)s %(message)s')

# Docs: https://circuitpython.readthedocs.io/projects/neopixel/en/latest/api.html
pixels = neopixel.NeoPixel(pin=pixel_pin, n=num_pixels, bpp=3, brightness=0.2, auto_write=True,
                           pixel_order=neopixel.GRB)

logging.info('Startup...')


GPIO.setwarnings(True)
GPIO.setup(motion_detect_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(motion_detect_pin, GPIO.RISING, callback=motionHandler)


water_level = WaterLevel()
temperature = Temperature()


#########################################


HttpServer(water_level)

# httpd.shutdown()
# httpd.server_close()

# while True:
#    logging.info('Sleep')
#    time.sleep(5)
