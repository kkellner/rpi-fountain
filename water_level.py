# Fountain project
#
# water_level.py - handle water level information
#


import logging
import time
import threading
import melopero_vl53l1x as mp
from enum import Enum


logger = logging.getLogger('water_level')

class WaterLevelState(Enum):

    FULL = (200, 90)         # Blink Green
    OK = (95, 40)            # Green
    LOW = (70, 20)           # Blink Yellow
    CRITICAL = (25, 5)       # Red
    EMPTY = (10, -100)        # Blink Red
    UNKNOWN = (1000, 1000)  # Gray

    # Value check starts at FULL and works it way down
    # Value must be within high-low range
    # once state is set, it can't change state until its no
    # longer in range of current state
    def __init__(self, high, low):
        self.high = high
        self.low = low


class WaterLevel:
    """Handle fountain water level operations"""

    # Distance between top of IR sensor and bottom of tube (in inches)
    TOTAL_DISTANCE_TO_BOTTOM = 16.3

    # The depth of water in which the fountain is considered to be full
    FULL_DEPTH = 11

    # The depth of water which no longer allows the pump to work
    EMPTY_DEPTH = 5

    def __init__(self, fountain):
        self.water_level_state = WaterLevelState.UNKNOWN
        self.water_depth = 0.0
        self.state_change_notify_list = []

        self.water_level_sensor = mp.VL53L1X()
        self.water_level_sensor.start_ranging(mp.VL53L1X.SHORT_DST_MODE)
        value_mm = self.water_level_sensor.get_measurement()
        if value_mm != -1:
            logger.info(
                "water level sensor initialized. Value: %s" % value_mm)
            monitor_water_level_thread = threading.Thread(
                target=self.__monitor_water_level)
            monitor_water_level_thread.daemon = True
            monitor_water_level_thread.start()
        else:
            logger.error("water level sensor initialize error")

    def get_depth(self):
        return self.water_depth

    def __set_depth(self, water_depth):
        self.water_depth = water_depth
        self.__refresh_state()

    def get_percent_full(self):
        """
        Calculate the percent of water tank full based on normal range.
        This means that the percent could be over 100% if fountain is overfull
        or it can be negative if its below the EMPTY_DEPTH acceptable for the pump
        """
        rawPercentValue = ((self.water_depth - WaterLevel.EMPTY_DEPTH) /
                           (WaterLevel.FULL_DEPTH - WaterLevel.EMPTY_DEPTH)) * 100

        return round(rawPercentValue, 1)
    
    def __refresh_state(self):
        """
        This method should be called upon every update of self.water_depth
        """
        percent_full = self.get_percent_full()
        # Check if current state is still correct
        current_state = self.water_level_state
        if percent_full <= current_state.high and percent_full >= current_state.low:
            # No state change
            return 

        # Current state is not correct, find current state
        current_state = None
        for state in WaterLevelState:
            # print('{:15} = {}'.format(state.name, state.low))
            if percent_full > state.low:
                current_state = state
                break
        if current_state is None:
            current_state = WaterLevelState.UNKNOWN

        logger.info('Update current water level state. Old: {} new:{}'.format(
            self.water_level_state.name, current_state.name))
        old_state = self.water_level_state
        self.water_level_state = current_state
        self.__notify_state_change(old_state, current_state)
        
    def get_state(self):
        return self.water_level_state

    def add_state_change_notify(self, callback):
        self.state_change_notify_list.append(callback)

    def __notify_state_change(self, oldState, newState):
        for notifyCallback in self.state_change_notify_list:
            notifyCallback(self, oldState, newState)

    def __monitor_water_level(self):
        t_end = 0
        while True:
            self.__set_depth(self.__calculate_water_depth())
            # Only print the water level every 3 seconds
            if time.time() > t_end:
                t_end = time.time() + 3
                logger.debug('Water depth: %.1f ' % self.water_depth)
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
        value_inches = (1/25.4) * middle_value_mm
        return value_inches
