# Fountain project
#
# water_level.py - handle water level information
#


import logging
import time
import threading
import melopero_vl53l1x as mp
from enum import Enum
import statistics
import schedule

logger = logging.getLogger('water_level')
fountain_data = logging.getLogger('fountain_data')


class WaterLevelState(Enum):

    FULL = (200, 90)         # Blink Green
    OK = (95, 40)            # Green
    LOW = (70, 20)           # Blink Yellow
    CRITICAL = (25, 5)       # Red
    EMPTY = (10, -100)       # Blink Red
    UNKNOWN = (1000, 1000)   # Gray

    # Value check starts at FULL and works it way down
    # Value must be within high-low range
    # once state is set, it can't change state until its no
    # longer in range of current state
    def __init__(self, high, low):
        self.high = high
        self.low = low


class WaterLevel:
    """Handle fountain water level operations"""

    MM_PER_INCH = 0.0393701

    # Distance between top of IR sensor and bottom of tube (in inches)
    TOTAL_DISTANCE_TO_BOTTOM_MM = 414
    TOTAL_DISTANCE_TO_BOTTOM_INCHES = TOTAL_DISTANCE_TO_BOTTOM_MM * MM_PER_INCH

    # The depth of water in which the fountain is considered to be full
    FULL_DEPTH_MM = 280
    FULL_DEPTH_INCHES = FULL_DEPTH_MM * MM_PER_INCH

    # The depth of water which no longer allows the pump to work
    EMPTY_DEPTH_MM = 114
    EMPTY_DEPTH_INCHES = EMPTY_DEPTH_MM * MM_PER_INCH

    def __init__(self, fountain):
        self.water_level_state = WaterLevelState.UNKNOWN
        self.water_depth_mm = 0
        self.state_change_notify_list = []

        self.water_level_sensor = mp.VL53L1X()
        self.water_level_sensor.setROI(6, 11, 10, 7)
        self.water_level_sensor.start_ranging(mp.VL53L1X.SHORT_DST_MODE)
        value_mm = self.water_level_sensor.get_measurement()
        if value_mm != -1:
            logger.info(
                "water level sensor initialized. Value: %s" % value_mm)
            # Update the depth first-time before we complete initalization
            self.__set_depth_mm(self.__calculate_water_depth_mm())
            monitor_water_level_thread = threading.Thread(
                target=self.__monitor_water_level)
            monitor_water_level_thread.daemon = True
            monitor_water_level_thread.start()

            # Docs: https://schedule.readthedocs.io/en/stable/
            # DOcs: https://github.com/dbader/schedule
            schedule.every().minute.at(":00").do(self.__log_data)

            # schedule.every().minute.do(self.__log_data)
            # schedule.every().hour.do(job)
            # schedule.every().day.at("10:30").do(job)
            # schedule.every(5).to(10).minutes.do(job)
            # schedule.every().monday.do(job)
            # schedule.every().wednesday.at("13:15").do(job)
            # schedule.every().minute.at(":17").do(job)

            self.__start_schedule_thread()

        else:
            logger.error("water level sensor initialize error")

    def get_depth_mm(self):
        return round(self.water_depth_mm, 1)

    def get_depth_inches(self):
        value_inches = (1/25.4) * self.water_depth_mm
        return round(value_inches, 1)

    def __set_depth_mm(self, water_depth_mm):
        # We only want to adjust the saved depth if its more then 1mm from current
        if self.water_depth_mm == water_depth_mm:
            # No change - do nothing
            return
        elif abs(self.water_depth_mm - water_depth_mm) == 2:
            newValue = self.water_depth_mm - ((self.water_depth_mm - water_depth_mm) / 2)
            logger.debug("XXXXX 2mm change of depth.  Old: %.f  Requested: %.f  Set to: %.f" %
                         (self.water_depth_mm, water_depth_mm, newValue))
            self.water_depth_mm = newValue
            self.__refresh_state()
        elif abs(self.water_depth_mm - water_depth_mm) > 2:

            logger.debug("XXXXX More then 2mm change of depth.  Old: %.f  New: %.f" %
                         (self.water_depth_mm, water_depth_mm))
            self.water_depth_mm = water_depth_mm
            self.__refresh_state()
        else:
            logger.debug("XXXXX Ignore water_depth_mm change because less then 2mm  Old: %.f  New: %.f" %
                         (self.water_depth_mm, water_depth_mm))

    def get_percent_full(self):
        """
        Calculate the percent of water tank full based on normal range.
        This means that the percent could be over 100% if fountain is overfull
        or it can be negative if its below the EMPTY_DEPTH acceptable for the pump
        """
        rawPercentValue = ((self.water_depth_mm - WaterLevel.EMPTY_DEPTH_MM) /
                           (WaterLevel.FULL_DEPTH_MM - WaterLevel.EMPTY_DEPTH_MM)) * 100

        return round(rawPercentValue, 0)

    def __refresh_state(self):
        """
        This method should be called upon every update of self.water_depth_mm
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

    def __start_schedule_thread(self):
        logging_thread = threading.Thread(
            target=self.__schedule_thread)
        logging_thread.daemon = True
        logging_thread.start()

    def __schedule_thread(self):
        while True:
            # self.__log_data()
            schedule.run_pending()
            time.sleep(1)

    def __log_data(self):
        fountain_data.info('Water depth: %.2f mm  Percent: %.0f' % (
            self.water_depth_mm, self.get_percent_full()))

    def __monitor_water_level(self):
        t_end = 0
        while True:
            self.__set_depth_mm(self.__calculate_water_depth_mm())
            # Only print the water level every 3 seconds
            if time.time() > t_end:
                t_end = time.time() + 3
                logger.debug('Water depth: %.1f mm' % self.water_depth_mm)
            time.sleep(1)

    def __calculate_water_depth_mm(self):
        distance_to_water = self.__measure_water_distance_mm()
        depth = WaterLevel.TOTAL_DISTANCE_TO_BOTTOM_MM - distance_to_water
        # The sensor is off a bit when dry. Make sure we don't have negative depth
        if depth < 0:
            depth = 0
        return depth

    def __measure_water_distance_mm(self):
        list = []
        samples = 15
        for x in range(samples):
            value_mm = self.water_level_sensor.get_measurement()
            list.append(value_mm)
            time.sleep(0.01)
        # list.sort()
        #middle_value_mm = list[int(samples/2)]
        #mean = round(statistics.mean(list),1)
        #mode = statistics.mode(list)
        middle_value_mm = statistics.median(list)

        logger.debug("Water: " + str(list) + " middle:" + str(middle_value_mm))
        #value_inches = (1/25.4) * middle_value_mm
        return middle_value_mm
