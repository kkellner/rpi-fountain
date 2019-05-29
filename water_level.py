# Fountain project
#
# water_level.py - handle water level information
#


import logging
import time
import threading
import melopero_vl53l1x as mp

class WaterLevel:
    """Handle fountain water level operations"""

    def __init__(self):
        self.water_level_sensor = mp.VL53L1X()
        logging.error("water_level_sensor: %s" % self.water_level_sensor)
        #self.water_level_sensor.start_ranging(mp.VL53L1X.SHORT_DST_MODE)

        #monitor_water_level_thread = threading.Thread(target=self.monitor_water_level)
        #monitor_water_level_thread.daemon = True
       # monitor_water_level_thread.start()


    def monitor_water_level(self):
        while True:
            self.water_level = self._calculateWaterDepth()
            logging.info('Water level: %.1f ' % self.water_level)
            time.sleep(3)


    def _calculateWaterDepth(self):
        list = []
        samples = 3
        for x in range(samples):
            value_mm = self.water_level_sensor.get_measurement()
            list.append(value_mm)
        list.sort()
        middle_value_mm = list[int(samples/2)]
        #print('values: ', list)
        value_inches = (1/25.4) * middle_value_mm
        return value_inches

    def getWaterDepth(self):
        return self.water_level