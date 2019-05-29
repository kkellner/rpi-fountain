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


class Display:
    """Handle fountain display operations"""

    # Configure GPIO pins
    motion_detect_pin = 17  # G17
    pixel_pin = board.D18

    # The number of NeoPixels
    num_pixels = 2

    display_auto_off_time_seconds = 3

    def __init__(self):
        self.display_off_timer = None
        # Docs: https://circuitpython.readthedocs.io/projects/neopixel/en/latest/api.html
        self.pixels = neopixel.NeoPixel(pin=Display.pixel_pin, n=Display.num_pixels, bpp=3, 
                        brightness=0.2, auto_write=True,
                        pixel_order=neopixel.GRB)


        self.pixels.fill((0, 0, 255))
                    
        # Configure motion detection
        GPIO.setup(Display.motion_detect_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(Display.motion_detect_pin, GPIO.RISING, callback=self.motionHandler)




    def motionHandler(self, channel):
        logging.info('In motionHandler channel: %s' % channel)
        if self.display_off_timer is not None:
            self.display_off_timer.cancel()

        self.pixels.fill((255, 0, 0))
        # pixels.show()
        self.display_off_timer = threading.Timer(
            Display.display_auto_off_time_seconds, self.turnOffDisplay)
        self.display_off_timer.daemon = True
        self.display_off_timer.start()

    def turnOffDisplay(self):
        logging.info('In turnOffDisplay')
        self.display_off_timer = None
        self.pixels.fill((0, 0, 0))

