import logging
import os
import time
import threading

#from geopy import distance
from pymavlink import mavutil, mavwp
# from dronekit import connect, VehicleMode, Command

class Navigation(object):

    def __init__(self, _rx_queue):
        self.rx_queue = _rx_queue

        self.__vehicle = None
        self.__alive = True


    def mode_listener(self, vehicle, attr_name, msg):
         """
            This function monitors the vehicle mode. If the vehicle is switched
            to STABALIZE or MANUAL mode, the companion computer immediately
            relinquishes control to the drone operator for manual flight.
         """
         logging.info("Mode engaged: [%s]" % (str(vehicle.mode.name)))

         if str(vehicle.mode.name) == "STABILIZED" or str(vehicle.mode.name) == "MANUAL":
            logging.critical("Killing companion computer process and relinquishing full control to flight operator")
            os._exit(0)
            # We should never ever ever get here.
            logging.critical("The program should have stopped running!")

    def run(self, is_downloading):

        #######################################################################
        # Connect to autopilot
        #######################################################################

        if (os.getenv('DEVELOPMENT') == 'True'):
            # PX4 SITL requires UDP port 14540
            connection_string = "udp:127.0.0.1:14540"
        else:
            connection_string = "/dev/ttyS0"

        logging.info("Connecting to vehicle on %s", connection_string)

        try:
            while self.__alive and self.__vehicle == None:
                try:
                    self.__vehicle = mavutil.mavlink_connection(connection_string)
                    self.__vehicle.wait_heartbeat()
                    logging.info("Connection to vehicle successful")
                except:
                    logging.error("Failed to connect to vehicle. Retrying...")
                    time.sleep(3)
        except Exception as e:
            logging.error("Connection to autopilot failed")
            logging.error(e)
            self.stop()

        #######################################################################
        # Set up killswitch
        #######################################################################

        # self.__vehicle.add_attribute_listener('mode', self.mode_listener)

        #######################################################################
        # Clear any existing mission and force mission upload
        #######################################################################

        logging.info("Clearing old mission from vehicle")
        self.__vehicle.waypoint_clear_all_send()
        self.__vehicle.recv_match(type=['MISSION_ACK'],blocking=True)
        logging.info("Mission cleared")

        #######################################################################
        # Wait for operator to upload mission
        #######################################################################

        logging.info("Waiting for mission upload...")

        waypoint_count = 0
        while waypoint_count < 1:
            logging.debug("Waiting for mission upload...")
            self.__vehicle.waypoint_request_list_send()
            msg = self.__vehicle.recv_match(type=['MISSION_COUNT'], blocking=False)
            if msg != None:
                waypoint_count = msg.count
            time.sleep(3)

        #######################################################################
        # Parsing for data station waypoints
        #######################################################################

        logging.info("Parsing data station waypoints...")

        for i in range(waypoint_count):
            self.__vehicle.waypoint_request_send(i)
            msg = self.__vehicle.recv_match(type=['MISSION_ITEM'], blocking=True)
            logging.debug("Receiving waypoint {0}".format(msg.seq))

        # self.__vehicle.mav.mission_ack_send(self.__vehicle.target_system, self.__vehicle.target_component, 0) # OKAY

        #######################################################################
        # Wait for operator to manually arm and switch the plane to AUTO
        #######################################################################

        logging.info("Waiting for vehicle arming...")
        while not self.__vehicle.motors_armed():
            time.sleep(3)
        logging.info("Vehicled armed")
        # while not self.__vehicle.armed and self.__alive:
        #     logging.debug("Waiting for vehicle arming...")
        #     time.sleep(3)
        #
        # logging.info("Waiting for operator to switch vehicle to AUTO")
        # while self.__vehicle.mode.name != "MAV_MODE_AUTO" and self.__alive:
        #     logging.debug("Waiting for AUTO mission start...")
        #     time.sleep(3)

        #######################################################################
        # In flight, wait for holding pattern over DS and switch out to continue
        # when the mission only when the download is complete.
        #######################################################################

        # try:
        #     while self.__alive:
        #         # Indefinite Hold mode represents loiter over data station
        #         # In certain failsafe modes, Hold may occur, but this is in "LAND"
        #         # mode in which position hold is the failsafe
        #         if self.__vehicle.mode.name == "HOLD":
        #             if not is_downloading.is_set(): # Done downloading
        #                 # TODO: Verify that this takes the plane to the next waypoint
        #                 self.__vehicle.mode.name = "MISSION"
        #
        # except Exception as e:
        #     logging.error("Error occurred in mission, returning home")
        #     # TODO: Verify RTL behavior is safe and reliable at long distances
        #     vehicle.mode.name = "RTL"
        #     vehicle.close()
        #     self.stop()

    def stop(self):
        logging.info("Stoping navigation...")
        if self.__vehicle != None:
            self.__vehicle.close()
        self._alive = False
