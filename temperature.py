# Fountain project
#
# temperature.py - handle temperature information
#

import logging
import time
import threading

from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import W1ThermSensorError, NoSensorFoundError, SensorNotReadyError


class Temperature:
    """Handle fountain temperature operations"""

    def __init__(self, fountain):


        # TODO: We need to handle case where sensor is not (yet) available
        try:
            self.water_temperature = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18B20, "011438959caa")
            self.fountain_temperature = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18B20, "0114388e73aa")
            self.circuit_temperature = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18S20, "0000003f9eff")

            monitor_temperature_thread = threading.Thread(
                target=self.monitor_temperature)
            monitor_temperature_thread.daemon = True
            monitor_temperature_thread.start()

        except NoSensorFoundError as e:
            logging.error(
                "Unable to initialize all temperature sensors. Error: " + str(e))


    def monitor_temperature(self):
        while True:
            wTemp = self.water_temperature.get_temperature(W1ThermSensor.DEGREES_F)
            fTemp = self.fountain_temperature.get_temperature(W1ThermSensor.DEGREES_F)
            cTemp = self.circuit_temperature.get_temperature(W1ThermSensor.DEGREES_F)
            logging.info(
                'Temperatures Water: %3.1f Fountain: %3.1f circuit: %3.1f', wTemp, fTemp, cTemp)
            time.sleep(6)


    def myfunc(self):
        logging.info("hello from myfunc")

