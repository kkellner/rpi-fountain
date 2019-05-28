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
from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import W1ThermSensorError, NoSensorFoundError, SensorNotReadyError
import melopero_vl53l1x as mp

import http.server
import socketserver
import json

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


def monitor_temperature():
    while True:
        wTemp = water_temperature.get_temperature(W1ThermSensor.DEGREES_F)
        fTemp = fountain_temperature.get_temperature(W1ThermSensor.DEGREES_F)
        cTemp = circuit_temperature.get_temperature(W1ThermSensor.DEGREES_F)
        logging.info(
            'Temperatures Water: %3.1f Fountain: %3.1f circuit: %3.1f', wTemp, fTemp, cTemp)
        time.sleep(6)


def monitor_water_level():
    while True:
        global water_level
        water_level = getWaterDepth()
        logging.info('Water level: %.1f ' % water_level)
        time.sleep(3)


def getWaterDepth():
    list = []
    samples = 3
    for x in range(samples):
        value_mm = water_level_sensor.get_measurement()
        list.append(value_mm)
    list.sort()
    middle_value_mm = list[int(samples/2)]
    #print('values: ', list)
    value_inches = (1/25.4) * middle_value_mm
    return value_inches


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

# TODO: We need to handle case where sensor is not (yet) available
try:
    water_temperature = W1ThermSensor(
        W1ThermSensor.THERM_SENSOR_DS18B20, "011438959caa")
    fountain_temperature = W1ThermSensor(
        W1ThermSensor.THERM_SENSOR_DS18B20, "0114388e73aa")
    circuit_temperature = W1ThermSensor(
        W1ThermSensor.THERM_SENSOR_DS18S20, "0000003f9eff")

    monitor_temperature_thread = threading.Thread(target=monitor_temperature)
    monitor_temperature_thread.daemon = True
    monitor_temperature_thread.start()

except NoSensorFoundError as e:
    logging.error("Unable to initialize all temperature sensors. Error: " + str(e))



water_level_sensor = mp.VL53L1X()
water_level_sensor.start_ranging(mp.VL53L1X.SHORT_DST_MODE)

monitor_water_level_thread = threading.Thread(target=monitor_water_level)
monitor_water_level_thread.daemon = True
monitor_water_level_thread.start()

#########################################

# Docs: https://docs.python.org/3/library/http.server.html
class GetRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Class for handling a request to the root path /
    """

    def do_GET(self):

        if self.path == '/':
            data = "Water level: %.1f" % water_level
            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            #self.send_header('Connection', 'Keep-Alive')
            self.send_header('Content-type', 'text/html')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(bytes(data, 'utf-8'))
            return

        elif self.path == '/v1':

                # Create the response
            response = {
                'water_level': water_level,
                'customer_id': 345,
                'location_id': 456,
            }

            response['note_text'] = "example text"

            data = json.dumps(response)

            # Write the response
            self.protocol_version = 'HTTP/1.1'
            self.send_response(200, 'OK')
            self.send_header('Connection', 'Keep-Alive')
            self.send_header('Content-type', 'application/json')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(bytes(data, 'utf-8'))
            return
        elif self.path == "/test":
             # serve the file!
            self.path = "testfile.txt"
            return http.server.SimpleHTTPRequestHandler.do_GET(self) 

    def do_POST(s):
        print('-----------------------')
        print('POST %s (from client %s)' % (s.path, s.client_address))
        print(s.headers)
        content_length = int(s.headers['Content-Length'])
        post_data = json.loads(s.rfile.read(content_length))
        print(json.dumps(post_data, indent=4, sort_keys=True))
        s.send_response(200)
        s.end_headers()


PORT = 80
#Handler = http.server.SimpleHTTPRequestHandler(directory="/")
#httpd = socketserver.TCPServer(("", PORT), Handler)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(('0.0.0.0', PORT), GetRequestHandler)
logging.info("serving at port: %d", PORT)

httpd.serve_forever(poll_interval=0.5)
logging.info("after serve_forever")

# httpd.shutdown()
# httpd.server_close()

# while True:
#    logging.info('Sleep')
#    time.sleep(5)
