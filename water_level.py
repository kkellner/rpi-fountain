# Fountain project
#
# water_level.py - handle water level information
#


import logging
import time
import threading
import melopero_vl53l1x as mp
from enum import Enum

class WaterStatus(Enum):
    WATER_LEVEL_UNKNOWN = -1
    WATER_LEVEL_EMPTY = 0       # Blink Red
    WATER_LEVEL_CRITICAL = 20   # Red
    WATER_LEVEL_LOW = 50        # Blink Yellow
    WATER_LEVEL_OK = 90         # Green
    WATER_LEVEL_FULL = 100      # Blink Green


class WaterLevel:
    """Handle fountain water level operations"""

    # Distance between top of IR sensor and bottom of tube (in inches)
    TOTAL_DISTANCE_TO_BOTTOM = 16.3

    # The depth of water in which the fountain is considered to be full
    FULL_DEPTH = 11

    # The depth of water which no longer allows the pump to work
    EMPTY_DEPTH = 5

    def __init__(self, fountain):
        self.water_depth = None

        self.water_level_sensor = mp.VL53L1X()
        self.water_level_sensor.start_ranging(mp.VL53L1X.SHORT_DST_MODE)
        value_mm = self.water_level_sensor.get_measurement()
        if value_mm != -1:
            logging.info(
                "water level sensor initialized. Value: %s" % value_mm)
            monitor_water_level_thread = threading.Thread(
                target=self.monitor_water_level)
            monitor_water_level_thread.daemon = True
            monitor_water_level_thread.start()
        else:
            logging.error("water level sensor initialize error")

    def get_depth(self):
        return self.water_depth

    def get_percent_full(self):
        """
        Calculate the percent of water tank full based on normal range.
        This means that the percent could be over 100% if fountain is overfull
        or it can be negative if its below the EMPTY_DEPTH acceptable for the pump
        """
        return ((self.water_depth - WaterLevel.EMPTY_DEPTH) / (WaterLevel.FULL_DEPTH - WaterLevel.EMPTY_DEPTH)) * 100

    def get_status(self):
        percent_full = self.get_percent_full()
        if percent_full <= WaterStatus.WATER_LEVEL_EMPTY.value:
            return WaterStatus.WATER_LEVEL_EMPTY
        elif percent_full <= WaterStatus.WATER_LEVEL_CRITICAL.value:
            return WaterStatus.WATER_LEVEL_CRITICAL
        elif percent_full <= WaterStatus.WATER_LEVEL_LOW.value:
            return WaterStatus.WATER_LEVEL_LOW
        elif percent_full <= WaterStatus.WATER_LEVEL_OK.value:
            return WaterStatus.WATER_LEVEL_OK
        elif percent_full <= WaterStatus.WATER_LEVEL_FULL.value:
            return WaterStatus.WATER_LEVEL_FULL

    def monitor_water_level(self):
        t_end = 0
        while True:
            self.water_depth = self.__calculate_water_depth()
            # Only print the water level every 3 seconds
            if time.time() > t_end:
                t_end = time.time() + 3
                logging.info('Water depth: %.1f ' % self.water_depth)
            time.sleep(1)

    def __calculate_water_depth(self):
        distance_to_water = self.__measure_water_distance()
        depth = WaterLevel.TOTAL_DISTANCE_TO_BOTTOM - distance_to_water
        # The sensor is off a bit when dry. Make sure we don't have negative depth
        if depth < 0:
            depth = 0
        return depth

    def __measure_water_distance(self):
        list = []
        samples = 3
        for x in range(samples):
            value_mm = self.water_level_sensor.get_measurement()
            list.append(value_mm)
        list.sort()
        middle_value_mm = list[int(samples/2)]
        # print('values: ', list)
        value_inches = (1/25.4) * middle_value_mm
        return value_inches
