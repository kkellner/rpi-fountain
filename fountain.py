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
from display import Display, Status
from http_request import HttpServer
from alert_monitor import AlertMonitor



class Fountain:
    """Handle fountain display operations"""

    def __init__(self):
        self.server = None
        self.display = None
        self.temperature = None
        self.water_level = None
        self.alert_monitor = None

        # Docs: https://docs.python.org/3/library/logging.html
        FORMAT = '%(asctime)-15s %(threadName)-10s %(levelname)6s %(message)s'
        logging.basicConfig(level=logging.NOTSET, format=FORMAT)

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        GPIO.setwarnings(True)


    def signal_handler(self, signal, frame):
        logging.info('Shutdown...')
        if self.server is not None:
            self.server.shutdown()
        if self.display is not None:
            self.display.shutdown()
        GPIO.cleanup()
        sys.tracebacklimit = 0
        sys.exit(0)

    def startup(self):
        logging.info('Startup...')
        self.display = Display(self)
        self.water_level = WaterLevel(self)
        self.temperature = Temperature(self)
        self.alert_monitor = AlertMonitor(self)

        self.alert_monitor.test()

        self.display.showStatus(Status.STARTUP, 2)
        #time.sleep(3)
        #self.display.showStatus(Status.WATER_LEVEL_OK, 2)
        #time.sleep(3)
        #display.showStatus(Status.WATER_LEVEL_LOW, 2)
        #time.sleep(3)
        #display.showStatus(Status.WATER_LEVEL_CRITICAL, 2)

        self.server = HttpServer(self)
        # the following is a blocking call
        self.server.run()

def main():
    """
    The main function
    :return:
    """
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")


    f = open("/proc/net/wireless", "rt")
    data = f.read()
    link = int(data[177:179])
    level = int(data[182:185])
    noise = int(data[187:192])

    print("Link:{} Level:{} Noise:{}".format(link, level, noise))

    fountain = Fountain()
    fountain.startup()


if __name__ == '__main__':
    main()
