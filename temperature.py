# Fountain project
#
# temperature.py - handle temperature information
#

import logging
import time
import threading

from w1thermsensor import W1ThermSensor
from w1thermsensor.errors import W1ThermSensorError, NoSensorFoundError, SensorNotReadyError

logger = logging.getLogger('temperature')


class Temperature:
    """Handle fountain temperature operations"""

    def __init__(self, fountain):
        self.water_temperature = None
        self.fountain_temperature = None
        self.circuit_temperature = None

        # TODO: We need to handle case where sensor is not (yet) available
        try:
            self.water_temperature_sensor = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18B20, "011438959caa")
            self.fountain_temperature_sensor = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18B20, "0114388e73aa")
            self.circuit_temperature_sensor = W1ThermSensor(
                W1ThermSensor.THERM_SENSOR_DS18S20, "0000003f9eff")

            monitor_temperature_thread = threading.Thread(
                target=self.monitor_temperature)
            monitor_temperature_thread.daemon = True
            monitor_temperature_thread.start()

        except NoSensorFoundError as e:
            logger.error(
                "Unable to initialize all temperature sensors. Error: " + str(e))


    def monitor_temperature(self):
        while True:
            self.water_temperature = self.__get_temperature(self.water_temperature_sensor)
            self.fountain_temperature = self.__get_temperature(self.fountain_temperature_sensor)
            self.circuit_temperature = self.__get_temperature(self.circuit_temperature_sensor)
            logger.debug(
                'Temperatures Water: %3.1f Fountain: %3.1f circuit: %3.1f', 
                self.water_temperature, self.fountain_temperature, self.circuit_temperature)
            time.sleep(6)

    def __get_temperature(self, sensor):
            return round(sensor.get_temperature(W1ThermSensor.DEGREES_F),1)