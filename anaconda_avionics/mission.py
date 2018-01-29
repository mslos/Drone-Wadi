"""
This is the main navigation script for a data mule mission. This program spawns three threads:
    1) navigation thread for directing the airplane to each camera locations
    2) image_download_script to manage the data tranfer from camera trap to drone
"""

import logging
import time

from collections import deque

# from Queue import Queue

from anaconda_avionics.microservices import Navigation

class Mission:

    __data_stations = None          # List of DataStation instances representing order of mission
    __landing_waypoints = None      # List of waypoints that must be followed for proper landing sequence

    __mission_queue = None          # Queue of data stations remaining in mission

    __download = None
    __navigation = None

    def __init__(self, _data_stations, _landing_waypoints):
        self.__data_stations = _data_stations
        self.__landing_waypoints = _landing_waypoints

        self.__data_stations_queue = deque(self.__data_stations)
        # self.__data_stations_queue.put(self.__data_stations)

        self.__navigation = Navigation(self.__data_stations_queue, self.__landing_waypoints)

    def log_data_station_status(self):
        summary = "Data stations summary: \n"
        for data_station in self.__data_stations:
            summary += data_station.summary()
        logging.info(summary)

    def start(self):
        """
           Start data retrieval mission
        """

        self.__navigation.start()

        while self.__navigation.isNavigationComplete:
            time.sleep(1)

        # Get final status of data stations
        self.log_data_station_status()
