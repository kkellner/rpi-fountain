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
import logging, logging.handlers 
import signal
import sys
import os
import psutil
from datetime import datetime

from temperature import Temperature
from water_level import WaterLevel
from display import Display, Status
from http_request import HttpServer
from notification import Notification
from rpi_info import RpiInfo
from pubsub import Pubsub

logger = logging.getLogger('fountain')


class Fountain:
    """Handle fountain display operations"""

    def __init__(self):
        self.pubsub = None
        self.server = None
        self.display = None
        self.temperature = None
        self.water_level = None
        self.notification = None
        self.rpi_info = None
        self.startup_complete = False

        # Docs: https://docs.python.org/3/library/logging.html
        # Docs on config: https://docs.python.org/3/library/logging.config.html
        FORMAT = '%(asctime)-15s %(threadName)-10s %(levelname)6s %(message)s'
        #logging.basicConfig(level=logging.NOTSET, format=FORMAT)
        logging.basicConfig(level=logging.INFO, format=FORMAT)
        self.__setup_logger("fountain_data", "/var/log/fountain_data.log")
        self.__setup_logger("fountain_water_state_change", "/var/log/fountain_water_state_change.log")
        self.__setup_logger("display_motion", "/var/log/fountain_display_motion.log")

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        GPIO.setwarnings(True)

    def __setup_logger(self, logger_name, log_file, level=logging.INFO):
        l = logging.getLogger(logger_name)
        FORMAT = '%(asctime)-15s %(message)s'
        formatter = logging.Formatter(FORMAT)
        # Docs: https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler
        fileHandler = logging.handlers.RotatingFileHandler(log_file, mode='a',
                                                           maxBytes=1000000, backupCount=2)
        fileHandler.setFormatter(formatter)
        l.setLevel(level)
        l.addHandler(fileHandler)
        l.propagate = False
  
    def signal_handler(self, signal, frame):
        logger.info('Shutdown...')
        if self.server is not None:
            self.server.shutdown()
        if self.display is not None:
            self.display.shutdown()
        if self.pubsub is not None:
            self.pubsub.shutdown()    
        GPIO.cleanup()
        sys.tracebacklimit = 0
        sys.exit(0)

    def startup(self):
        logger.info('Startup...')

        self.display = Display(self)
        self.display.showStatus(Status.STARTUP, 2)

        self.pubsub = Pubsub(self)
        self.rpi_info = RpiInfo(self)
        self.water_level = WaterLevel(self)
        self.temperature = Temperature(self)
        self.notification = Notification(self)

        self.startup_complete = True
        self.__start_publish_status_thread()

        self.server = HttpServer(self)
        # the following is a blocking call
        self.server.run()

    def __start_publish_status_thread(self):
        logging_thread = threading.Thread(
            target=self.__publish_status_thread)
        logging_thread.daemon = True
        logging_thread.start()

    def __publish_status_thread(self):
        while True:
            self.publish_current_state()
            time.sleep(60)


    def publish_current_state(self):

        if not self.startup_complete:
            return

        water_depth_mm = self.water_level.get_depth_mm()
        water_depth_inches = self.water_level.get_depth_inches()
        water_percent_full = self.water_level.get_percent_full()
        water_depth_state = self.water_level.get_state()

        rpiInfo = self.rpi_info.get_info()

        #self.temperature.water_temperature

        data = {
                "waterLevelPercentFull": water_percent_full,
                "waterLevelState": water_depth_state.name,
                "waterTemperature": self.temperature.water_temperature,
                "fountainTemperature": self.temperature.fountain_temperature,
                "circuitTemperature": self.temperature.circuit_temperature,
                "waterDepth": water_depth_inches,
                "waterDepth_inches": water_depth_inches,
                "waterDepth_mm": water_depth_mm,
                "cpuPercent": psutil.cpu_percent(),
                "rpiTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "rpiInfo": rpiInfo,
                "temp_distance_to_water_mm": self.water_level.temp_distance_to_water_mm
            }

        #data = json.dumps(response)
        self.pubsub.publishStatus(data)


def main():
    """
    The main function
    :return:
    """
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

    # f = open("/proc/net/wireless", "rt")
    # data = f.read()
    # link = int(data[177:179])
    # level = int(data[182:185])
    # noise = int(data[187:192])
    # print("Link:{} Level:{} Noise:{}".format(link, level, noise))

    fountain = Fountain()
    fountain.startup()


if __name__ == '__main__':
    main()
