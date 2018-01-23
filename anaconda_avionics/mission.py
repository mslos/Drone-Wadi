"""
This is the main navigation script for a data mule mission. This program spawns three threads:
    1) navigation thread for directing the airplane to each camera locations
    2) image_download_script to manage the data tranfer from camera trap to drone
"""

import threading
import logging
from Queue import Queue, Empty

from anaconda_avionics.microservices import Download
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

        # mission_queue is accessible to both threads and is used for inter-thread communication
        self.__mission_queue = Queue()
        self.__mission_queue.put(self.__data_stations)

        # These are the two threads running in parallel. Running as threads ensures a level of robustness against
        # unexpected shutdown of either thread (especially the non-critical download thread).
        self.__download = Download(self.__mission_queue)
        self.__navigation = Navigation(self.__mission_queue, self.__landing_waypoints)

    def log_data_station_status(self):
        summary = "Data stations summary: \n"
        for data_station in self.__data_stations:
            summary += data_station.summary()
        logging.info(summary)

    def start(self):
        """
           Method for starting a data retrieval mission for Data Mule
        """
        navigation_thread = threading.Thread(
            target=self.__navigation.start(),
            args=(self.__mission_queue, self.__landing_waypoints),
            name="NAVIGATION")

        download_thread = threading.Thread(
            target=self.__download.start(),
            args=(self.__mission_queue),
            name="DOWNLOAD")

        navigation_thread.start()
        download_thread.start()

        # FIXME: what does this do? Is there a more efficient way to know when all data stations have been visited?
        while True:
            try:
                self.__mission_queue.get_nowait()
                break
            except Empty:
                pass

        # Get final status of data stations
        self.log_data_station_status()
