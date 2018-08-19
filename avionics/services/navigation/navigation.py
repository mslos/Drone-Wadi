import logging
import os
import time
import threading

from geopy import distance
from pymavlink import mavutil, mavwp
from dronekit import connect

class Navigation(object):

    STANDARD_WAYPOINT_COMMAND = 16
    LOITER_WAYPOINT_COMMAND = 17
    ROI_WAYPOINT_COMMAND = 201

    def __init__(self, _rx_queue):
        self.rx_queue = _rx_queue

        self.__vehicle = None
        self.__alive = True

    def wait_flight_distance(self, dist, waypoint, data_station_id):
        while True:

            # Avoid calculations on "None"
            if (self.__vehicle.location.global_relative_frame.lat == None):
                logging.debug("No GPS data, moving ahead with download sequence...")
                return

            cur_lat = self.__vehicle.location.global_relative_frame.lat
            cur_lon = self.__vehicle.location.global_relative_frame.lon

            wp_lat = waypoint.x
            wp_lon = waypoint.y

            # Get distance between current waypoint and data station in meters
            d = distance.distance((cur_lat, cur_lon), (wp_lat, wp_lon)).m

            logging.debug("Distance to data station %s: %s m" % (data_station_id, round(d)))

            if (d < dist):
                logging.info("Data station %s less than %s away" % (data_station_id, dist))
                return
            else:
                time.sleep(1)

    def run(self, wakeup_event, download_event, new_ds, is_downloading, led_status):

        #######################################################################
        # Connect to autopilot
        #######################################################################

        if (os.getenv('DEVELOPMENT') == 'True'):
            # PX4 SITL requires UDP port 14540
            connection_string = "udp:127.0.0.1:14540"
        else:
            connection_string = "/dev/ttyACM0"

        logging.info("Connecting to vehicle on %s", connection_string)
        # led_status.put("PENDING")

        try:
            self.__vehicle = connect(connection_string, baud=115200, wait_ready=True)
            logging.info("Connection to vehicle successful")
        except:
            logging.error("Failed to connect to vehicle. Retrying...")
            time.sleep(3)

        # while self.__alive == True and self.__vehicle == None:
        #     try:
        #         self.__vehicle = connect(connection_string, baud=115200, wait_ready=True)
        #         logging.info("Connection to vehicle successful")
        #         break
        #     except:
        #         logging.error("Failed to connect to vehicle. Retrying...")
        #         time.sleep(3)

        # led_status.put("READY")

        # Continously monitor state of autopilot and kick of download when necessary
        current_waypoint = 0
        waypoints = []
        logging.debug("Before while")
        while self.__alive:
            # Get most up-to-date mission
            logging.debug("In while")
            waypoints = self.__vehicle.commands
            waypoints.download()
            logging.debug("Before wait")
            waypoints.wait_ready()

            waypoint_count = len(waypoints)

            # Zero base index into waypoints list
            current_waypoint = self.__vehicle.commands.next-1
            logging.debug("Current waypoint: %s", current_waypoint)

            # If we are en route to a data station (marked as LOITER waypoint followed by an ROI)
            if (waypoint_count-current_waypoint > 1) and \
                (waypoints[current_waypoint].command == self.LOITER_WAYPOINT_COMMAND) and \
                (waypoints[current_waypoint+1].command == self.ROI_WAYPOINT_COMMAND):
                # By default, PX4 uses floats. We use strings (of rounded integers) for data station IDs
                data_station_id = str(int(waypoints[current_waypoint+1].param3))

                logging.info("En route to data station: %s", data_station_id)

                # Pass the data station ID to the data station handler
                self.rx_queue.put(data_station_id)
                new_ds.set()

                # Give the DataStationHandler some time to kick off the download
                time.sleep(5)

                self.wait_flight_distance(5000, waypoints[current_waypoint], data_station_id)
                logging.info("Beginning XBee wakeup from data station %s...", data_station_id)

                # Tell the data station handler to begin wakeup
                wakeup_event.set()

                self.wait_flight_distance(1000, waypoints[current_waypoint], data_station_id)
                logging.info("Beginning data download from data station %s...", data_station_id)

                # Tell the data stataion handler to begin download
                download_event.set()

                while is_downloading.is_set():
                    logging.debug("Downloading...")
                    time.sleep(3)

                wakeup_event.clear()
                download_event.clear()

                # Skip the ROI point
                next_waypoint = current_waypoint+2
                logging.info("Done downloading. Moving on to waypoint %i...", (next_waypoint+1))
                self.__vehicle.commands.next = next_waypoint

            else:
                logging.debug("Not at data station...")
                time.sleep(3)

    def stop(self):
        logging.info("Stoping navigation...")
        self.__alive = False
        if self.__vehicle != None:
            self.__vehicle.close()
