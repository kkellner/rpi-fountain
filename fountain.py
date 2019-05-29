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


def main():
    """
    The main function
    :return:
    """

    # Docs: https://docs.python.org/3/library/logging.html
    FORMAT = '%(asctime)-15s %(threadName)s %(levelname)6s %(message)s'
    logging.basicConfig(level=logging.NOTSET, format=FORMAT)

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

    display = Display()
    water_level = WaterLevel()
    temperature = Temperature()
 
    #########################################

    server = HttpServer(water_level)
    # the following is a blocking call
    server.run()

    # while True:
    #    logging.info('Sleep')
    #    time.sleep(5)



if __name__ == '__main__':
    main()
