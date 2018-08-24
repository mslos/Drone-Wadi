import logging
import os
import serial
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

    def run(self, wakeup_event, download_event, new_ds, is_downloading, is_awake, led_status):

        #######################################################################
        # Connect to the autopilot
        #######################################################################

        if (os.getenv('DEVELOPMENT') == 'True'):
            # PX4 SITL requires UDP port 14540
            connection_string = "udp:127.0.0.1:14540"
        else:
            connection_string = "/dev/ttyACM0"

        logging.info("Connecting to vehicle on %s", connection_string)
        led_status.put("PENDING")

        while self.__alive == True and self.__vehicle == None:
            try:
                # Verify that the serial port is cleared
                s = serial.Serial("/dev/ttyACM0", baudrate=115200)
                s.close()
                time.sleep(3) # CLOSE PLS
                logging.info("Cleared serial port")

                self.__vehicle = connect(connection_string, baud=115200, wait_ready=True)
                logging.info("Connection to vehicle successful")
                break
            except:
                logging.error("Failed to connect to vehicle. Retrying...")
                led_status.put("FAILURE")
                time.sleep(3)

        time.sleep(3) # Verify LEDs

        #######################################################################
        # Monitor location relative to next data station to instruct the data
        # station handler to step through the wakeup and download process
        # when most efficient
        #######################################################################

        # Continously monitor state of autopilot and kick of download when necessary
        current_waypoint = 0
        waypoints = []
        while self.__alive:
            # Get most up-to-date mission
            try:
                waypoints = self.__vehicle.commands

                # THE MAGIC BULLET! Why does this make it work? Beats me.
                # Nevertheless, this needs to be called before download.
                waypoints.clear()

                waypoints.download()
                waypoints.wait_ready()
                led_status.put("READY") # Not truly ready until waypoint download works

            except:
                logging.error("Waypoint download failure")
                led_status.put("FAILURE")

            waypoint_count = len(waypoints)

            next_data_station_index = None

            # Filter for next data station
            for i in range(waypoint_count):
                # A data station is marked as LOITER waypoint followed by a DO_SET_ROI
                if waypoints[i].command == self.LOITER_WAYPOINT_COMMAND and \
                    waypoints[i+1].command == self.ROI_WAYPOINT_COMMAND:
                    next_data_station_index = i
                    break

            # No more data stations to service
            if next_data_station_index != None:

                # By default, PX4 uses floats. We use strings (of rounded integers) for data station IDs
                data_station_id = str(int(waypoints[next_data_station_index+1].param3))

                logging.info("En route to data station: %s", data_station_id)

                # Pass the data station ID to the data station handler
                self.rx_queue.put(data_station_id)

                # Let the data station handler know there's a new station to service
                new_ds.set()

                # Give the data station hander some time to pick up the new data station ID
                time.sleep(5)

                # Wait until the sUAS is within 5000 m (5 km) of the data station for XBee wakeup
                self.wait_flight_distance(5000, waypoints[next_data_station_index], data_station_id)
                logging.info("Beginning XBee wakeup from data station %s...", data_station_id)

                # Tell the data station handler to begin wakeup
                wakeup_event.set()

                # Wait until the sUAS is within 1000 m (1 km) of the data station for SFTP download
                self.wait_flight_distance(1000, waypoints[next_data_station_index], data_station_id)
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
                logging.debug("No more data stations in mission...")
                time.sleep(5)


    def stop(self):
        logging.info("Stoping navigation...")
        self.__alive = False
        if self.__vehicle != None:
            self.__vehicle.close()
            time.sleep(3) # CLOSE PLS
