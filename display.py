# Fountain project
#
# display.py - handle display updates (NeoPixel)
#

import logging
import time
import threading
import board
import RPi.GPIO as GPIO
import neopixel
from enum import Enum


class Status(Enum):
    NONE = 0
    STARTUP = 1
    SHUTDOWN = 2
    ERROR = 3
    WATER_LEVEL_UNKNOWN = 10
    WATER_LEVEL_EMPTY = 11      # Blink Red
    WATER_LEVEL_CRITICAL = 12   # Red
    WATER_LEVEL_LOW = 13        # Blink Yellow
    WATER_LEVEL_OK = 14        # Green
    WATER_LEVEL_FULL = 15      # Blink Green




class Color:
    RED = (255, 0, 0)
    YELLOW = (255, 200, 0)
    GREEN = (0, 255, 0)
    AQUA = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (255, 0, 255)
    BLACK = (0, 0, 0)


class Display:
    """Handle fountain display operations"""

    # Configure GPIO pins
    motion_detect_pin = 17  # G17
    pixel_pin = board.D18

    # The number of NeoPixels
    num_pixels = 2

    display_auto_off_time_seconds = 3

    def __init__(self, fountain):
        self.fountain = fountain
        self.display_off_timer = None
        self.status = Status.NONE
        self.display_status_thread = None
        self.display_status_thread_stop = False
        # Docs: https://circuitpython.readthedocs.io/projects/neopixel/en/latest/api.html
        self.pixels = neopixel.NeoPixel(pin=Display.pixel_pin, n=Display.num_pixels, bpp=3,
                                        brightness=0.2, auto_write=False,
                                        pixel_order=neopixel.GRB)

        # Configure motion detection
        GPIO.setup(Display.motion_detect_pin, GPIO.IN,
                   pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(Display.motion_detect_pin,
                              GPIO.RISING, callback=self.motionHandler)

    def shutdown(self):
        self._stop_display_status_thread()
        self.turnOffDisplay()

    def motionHandler(self, channel):
        logging.info('In motionHandler channel: %s' % channel)
        self._stop_display_off_timer()

        water_depth_status = self.fountain.water_level.get_status()
        logging.info("water_depth_status: %s" % water_depth_status)
        displayStatus = Status[water_depth_status.name]
        self.showStatus(displayStatus, 0)

        self.display_off_timer = threading.Timer(
            Display.display_auto_off_time_seconds, self.turnOffDisplay)
        self.display_off_timer.daemon = True
        self.display_off_timer.start()

    def _stop_display_off_timer(self):
        if self.display_off_timer is not None:
            self.display_off_timer.cancel()
        self.display_off_timer = None

    def turnOffDisplay(self):
        logging.info('In turnOffDisplay')
        self._stop_display_off_timer()
        self._stop_display_status_thread()
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def showStatus(self, status: Status, showForSeconds=2):

        self.status = status
        logging.info('Set display status: %s' % status)

        self._stop_display_status_thread()

        self.display_status_thread_stop = False
        self.display_status_thread = threading.Thread(
            target=self._displayStatus,
            args=[showForSeconds])
        self.display_status_thread.daemon = True
        self.display_status_thread.start()

    def _stop_display_status_thread(self):
        if self.display_status_thread is threading.current_thread():
            return
        if self.display_status_thread is not None:
            logging.info('Stop thread request')
            self.display_status_thread_stop = True
            self.display_status_thread.join()
            self.display_status_thread = None
            logging.info('Stop thread complete')

    def _displayStatus(self, showForSeconds):

        sequenceMethod = getattr(self, '_' + self.status.name + '_Sequence')
        t_end = time.time() + showForSeconds
        while not self.display_status_thread_stop and (showForSeconds == 0 or time.time() < t_end):
            sequenceMethod()

        self.turnOffDisplay()

    def _STARTUP_Sequence(self):
        speed = 0.001
        for i in range(255):
            if self.display_status_thread_stop:
                break
            self.pixels[0] = (0, 0, i)
            self.pixels[1] = (0, 0, 255-i)
            self.pixels.show()
            time.sleep(speed)
        for i in range(255):
            if self.display_status_thread_stop:
                break
            self.pixels[0] = (0, 0, 255-i)
            self.pixels[1] = (0, 0, i)
            self.pixels.show()
            time.sleep(speed)

    def _ERROR_Sequence(self):
        speed = 0.2
        self.pixels[0] = Color.RED
        self.pixels[1] = Color.BLACK
        self.pixels.show()
        time.sleep(speed)
        self.pixels[0] = Color.BLACK
        self.pixels[1] = Color.RED
        self.pixels.show()
        time.sleep(speed)

    def _WATER_LEVEL_FULL_Sequence(self):
        speed = 0.2
        self.pixels[0] = Color.GREEN
        self.pixels[1] = Color.BLACK
        self.pixels.show()
        time.sleep(speed)
        self.pixels[0] = Color.BLACK
        self.pixels[1] = Color.GREEN
        self.pixels.show()
        time.sleep(speed)

    def _WATER_LEVEL_OK_Sequence(self):
        speed = 0.1
        self.pixels[0] = Color.GREEN
        self.pixels[1] = Color.GREEN
        self.pixels.show()
        time.sleep(speed)

    def _WATER_LEVEL_LOW_Sequence(self):
        speed = 0.2
        self.pixels[0] = Color.YELLOW
        self.pixels[1] = Color.YELLOW
        self.pixels.show()
        time.sleep(speed)
        self.pixels[0] = Color.BLACK
        self.pixels[1] = Color.BLACK
        self.pixels.show()
        time.sleep(speed)

    def _WATER_LEVEL_CRITICAL_Sequence(self):
        speed = 0.1
        self.pixels[0] = Color.RED
        self.pixels[1] = Color.RED
        self.pixels.show()
        time.sleep(speed)

    def _WATER_LEVEL_EMPTY_Sequence(self):
        speed = 0.2
        self.pixels[0] = Color.RED
        self.pixels[1] = Color.BLACK
        self.pixels.show()
        time.sleep(speed)
        self.pixels[0] = Color.BLACK
        self.pixels[1] = Color.RED
        self.pixels.show()
        time.sleep(speed)


    def _WATER_LEVEL_OK_pulse_Sequence(self):
        speed = 0.001
        for i in range(255):
            if self.display_status_thread_stop:
                break
            self.pixels[0] = (0, i, 0)
            self.pixels[1] = (0, 255-i, 0)
            self.pixels.show()
            time.sleep(speed)
        for i in range(255):
            if self.display_status_thread_stop:
                break
            self.pixels[0] = (0, 255-i, 0)
            self.pixels[1] = (0, i, 0)
            self.pixels.show()
            time.sleep(speed)
