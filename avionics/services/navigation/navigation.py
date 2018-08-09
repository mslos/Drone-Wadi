import logging
import time
import threading

#from geopy import distance
from pymavlink import mavutil
from dronekit import connect, VehicleMode, Command

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

         if str(vehicle.mode.name) == "STABILIZE" or str(vehicle.mode.name) == "MANUAL":
            logging.critical("Killing companion computer process and relinquishing full control to flight operator")
            os._exit(0)
            # We should never ever ever get here.
            logging.critical("The program should have stopped running!")

    # @vehicle.on_message('MISSION_ACK')
    # def mission_ack_listener(self, name, message):
    #     """
    #         Listens for a MISSION_ACK MAVLINK message from the autopilot confirming
    #         a mission upload. The newly uploaded mission is then parsed for
    #         data station ROIs.
    #     """
    #     pass

    def run(self, is_downloading):

        #######################################################################
        # Connect to autopilot
        #######################################################################

        if (os.getenv('TESTING') == 'True'):
            connection_string = "udp:127.0.0.1:14540"
        else:
            connection_string = "/dev/ttyS0"

        logging.info("Connecting to vehicle on %s", connection_string)

        try:
            while self.__alive:
                try:
                    self.__vehicle = connect(connection_string, baud=57600, wait_ready=True)
                    logging.info("Connection to vehicle successful")
                    break
                except:
                    logging.error("Failed to reconnect to vehicle. Retrying...")
        except Exception as e:
            logging.error("Connection to autopilot failed")
            logging.error(e)
            self.stop()

        #######################################################################
        # Wait for operator to manually arm and switch the plane to AUTO
        #######################################################################

        logging.info("Waiting for vehicle arming...")
        while not self.__vehicle.armed and self.__alive:
            logging.debug("Waiting for vehicle arming...")

        logging.info("Waiting for operator to switch vehicle to AUTO")
        while self.__vehicle.mode != VehicleMode("AUTO") and self.__alive:
            logging.debug("Waiting for AUTO mission start...")

        #######################################################################
        # In flight, wait for holding pattern over DS and switch out to continue
        # when the mission only when the download is complete.
        #######################################################################

        try:
            while self.__alive:
                # Indefinite Hold mode represents loiter over data station
                # In certain failsafe modes, Hold may occur, but this is in "LAND"
                # mode in which position hold is the failsafe
                if self.__vehicle.mode.name == "HOLD":
                    if not is_downloading.is_set(): # Done downloading
                        # TODO: Verify that this takes the plane to the next waypoint
                        self.__vehicle.mode.name = "MISSION"

        except Exception as e:
            logging.error("Error occurred in mission, returning home")
            # TODO: Verify RTL behavior is safe and reliable at long distances
            vehicle.mode.name = "RTL"
            vehicle.close()
            self.stop()

    def stop(self):
        logging.info("Stoping navigation...")
        self._alive = False
