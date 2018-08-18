import logging
import os
import time
import threading

from geopy import distance
from pymavlink import mavutil, mavwp

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
            self.__vehicle.wait_gps_fix()
            self.__vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=True)

            cur_lat = self.__vehicle.messages['GPS_RAW_INT'].lat*1.0e-7
            cur_lon = self.__vehicle.messages['GPS_RAW_INT'].lon*1.0e-7

            wp_lat = waypoint.x
            wp_lon = waypoint.y

            # Get distance between current waypoint and data station in meters
            d = distance.distance((cur_lat, cur_lon), (wp_lat, wp_lon)).m

            logging.debug("Distance to data station %s: %s m" % round(data_station_id, d))

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
        led_status.put("PENDING")

        while self.__alive == True and self.__vehicle == None:
            try:
                self.__vehicle = mavutil.mavlink_connection(connection_string, autoreconnect=True)
                self.__vehicle.wait_heartbeat()
                logging.info("Connection to vehicle successful")
            except:
                logging.error("Failed to connect to vehicle. Retrying...")
                time.sleep(3)

        logging.info("Here")

        led_status.put("READY")
        # Continously monitor state of autopilot and kick of download when necessary

        current_waypoint = 0
        waypoints = []
        while self.__alive:
            # Get most up-to-date mission
            self.__vehicle.waypoint_request_list_send()
            waypoint_count = self.__vehicle.recv_match(type=['MISSION_COUNT'], blocking=True).count

            waypoints = []
            for i in range(waypoint_count):
                self.__vehicle.waypoint_request_send(i)
                wp = self.__vehicle.recv_match(type=['MISSION_ITEM'], blocking=True)
                waypoints.append(wp)
                # logging.debug(wp)

            # Update current_waypoint
            m = self.__vehicle.recv_match(type='MISSION_CURRENT', blocking=True)
            current_waypoint = m.seq

            # If we are en route to a data station (marked as LOITER waypoint followed by an ROI)
            if (waypoints[current_waypoint].command == self.LOITER_WAYPOINT_COMMAND) and \
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
                self.__vehicle.waypoint_set_current_send(next_waypoint)

            else:
                logging.debug("Not at data station...")
                time.sleep(3)

    def stop(self):
        logging.info("Stoping navigation...")
        self.__alive = False
        if self.__vehicle != None:
            self.__vehicle.close()
