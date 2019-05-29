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
import logging
import signal
import sys
import os

from temperature import Temperature
from water_level import WaterLevel
from display import Display
from http_request import HttpServer


server = None

# Docs: https://docs.python.org/3/library/logging.html
logging.basicConfig(level=logging.NOTSET,
                    format='%(asctime)-15s %(threadName)s %(message)s')

def signal_handler(signal, frame):
    global display
    logging.info('Shutdown...')
    GPIO.cleanup()
    if server is not None:
        server.shutdown()
    sys.tracebacklimit = 0
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)



logging.info('Startup...')

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")


GPIO.setwarnings(True)

water_level = WaterLevel()
#temperature = Temperature()
display = Display()

#########################################


# TODO: Currently this is blocking -- need to make threaded so its non-blocking
server = HttpServer(water_level)

# httpd.shutdown()
# httpd.server_close()

# while True:
#    logging.info('Sleep')
#    time.sleep(5)
