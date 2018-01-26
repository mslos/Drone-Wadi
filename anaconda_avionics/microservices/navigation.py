import math
import os
import time
import threading
import logging

from pymavlink import mavutil
from dronekit import connect, VehicleMode, Command
from Queue import Empty

from anaconda_avionics.microservices import Download
from anaconda_avionics.utilities import Timer
from anaconda_avionics.utilities import Xbee

class Navigation(object):

    # -----------------------
    # Constants
    # -----------------------

    # TODO: grab these constants from those set on vehicle itself
    AIRSPEED_SLOW = 15
    AIRSPEED_MED = 20
    AIRSPEED_FAST = 40
    DOWNLOAD_TIMEOUT = 240

    # -----------------------
    # Private variables
    # -----------------------

    __data_stations = None          # List of data stations to be visited
    __xbee = None                   # Xbee comm module
    __vehicle = None                # Dronekit vehicle reference

    __data_stations_queue = None    # Queue of data stations to be visited
    __landing_waypoints = None      # Queue of landing waypoints to be visited on landing approach

    # -----------------------
    # Public variables
    # -----------------------

    isNavigationComplete = False    # Allow Mission class to know when navigation has finished

    def __init__(self, _data_stations_queue, _landing_waypoints):
        self.__data_stations_queue = _data_stations_queue
        self.__landing_waypoints = _landing_waypoints

        # Create and connect to xBee module
        self.__xbee = Xbee()  # Create and connect to xBee module

    # -----------------------
    # General utility methods
    # -----------------------

    # TODO: rework for less nuclear option--no os.exit(0)
    def mode_callback(self, vehicle, attr_name, msg):
         """
            This function monitors the vehicle mode. If the vehicle is switched to STABALIZE, the companion computer
            (Raspberry Pi) immediately relinquishes control to drone operator for manual operation.
         """
         logging.info("Mode engaged: [%s]" % (str(vehicle.mode.name)))

         if str(vehicle.mode.name) == "STABILIZE":  # Quit program entirely to silence Raspberry Pi
             logging.critical("Killing program and relinquishing control to flight operator.")
             os._exit(0)  # pylint: disable=protected-access
             #  We should never ever ever get here!

    # TODO: There must be a better way to do this... See: Vincenty's formulae (GeoPy package)
    def get_distance_meters(self, location_1, location_2):
        """
            Calculate distance between two GPS coordinates

            Returns the ground distance in metres between two LocationGlobal objects.
            This method is an approximation, and will not be accurate over large distances and close to the
            earth's poles. It comes from the ArduPilot test code:
            https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
        """
        dlat = location_2.lat - location_1.lat
        dlong = location_2.lon - location_1.lon
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

    # -----------------------
    # Mission preparation
    # -----------------------

    def connectToAutopilot(self):
        """
        Connect companion computer to Pixhawk autopilot
        :return:
        """
        # Set up connection with Pixhawk autopilot
        if not "DEVELOPMENT" in os.environ: # When not in development mode, connect to real Pixhawk
            connection_string = "/dev/ttyS0"
        else:  # in development mode, connect to plane over SITL (tcp:127.0.0.1:5760)
            connection_string = "tcp:127.0.0.1:5760"

        logging.debug('Connecting to vehicle on: %s' % connection_string)

        while True:
            try:
                self.__vehicle = connect(connection_string, baud=57600, wait_ready=True)
                break
            except:
                logging.error("Failed to connect to vehicle. Retrying connection...")

        logging.info('Connection to vehicle successful')

    def uploadMission(self, vehicle, data_stations_queue, landing_waypoints):
        """
        Uploads route that the drone will take to service the requested camera traps
        as a series of MAVLink commands to the autopilot.
        """

        cmds = vehicle.commands

        logging.info("Downloading mission...")
        cmds.download()
        cmds.wait_ready()

        logging.info("Clearing existing commands on autopilot...")
        cmds.clear()

        #  Add takeoff command
        logging.info("Adding takeoff command...")
        cmds.add(Command(0,
                         0,
                         0,
                         mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                         mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                         0,
                         0,
                         30,
                         0,
                         0,
                         0,
                         0,
                         0,
                         30))

        #  Add camera trap locations as unlimited loiter commands. The aircraft will
        #  fly to the GPS coordinate and circle them indefinitely. The autopilot
        #  proceed to the next mission item after vehicle mode is switched out of
        #  AUTO and back into AUTO.
        logging.info("Adding new waypoint commands...")

        # TODO: get rid of this clunky code segment
        while True:
            try:
                cameras = data_stations_queue.get_nowait()
                break
            except Empty:
                pass

        for cam in cameras:
            logging.info('New Camera:\n%s' % cam.summary())
            cmds.add(Command(0,
                             0,
                             0,
                             mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                             mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                             0,
                             0,
                             0,
                             0,
                             0,
                             0,
                             cam.lat,
                             cam.lon,
                             cam.alt))

        # Add landing sequence
        logging.info("Adding landing sequence...")

        #  Start landing Sequence
        logging.info("Adding start landing command...")
        cmds.add(Command(0,
                         0,
                         0,
                         mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                         mavutil.mavlink.MAV_CMD_DO_LAND_START,
                         0,
                         0,
                         0,
                         0,
                         0,
                         0,
                         0,
                         0,
                         0))

        #  Approach runway
        landing = landing_waypoints.pop()
        logging.info("Adding runway approach waypoints...")
        for waypoint in landing_waypoints:
            logging.info('New Waypoint:\n%s' % waypoint.summary())
            cmds.add(Command(0,
                             0,
                             0,
                             mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                             mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                             0,
                             0,
                             0,
                             0,
                             0,
                             0,
                             waypoint.lat,
                             waypoint.lon,
                             waypoint.alt))

        # Execute landing operation
        logging.info("Adding landing command...")
        logging.info('Landing Target:\n%s' % landing.summary())
        cmds.add(Command(0,
                         0,
                         0,
                         mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                         mavutil.mavlink.MAV_CMD_NAV_LAND,
                         0,
                         0,
                         0,
                         0,
                         0,
                         0,
                         landing.lat,
                         landing.lon,
                         0))

        #  Upload mission
        logging.info("Uploading full loiter mission...")

        cmds.upload()
        cmds.wait_ready()

        logging.info("Mission upload successful")


    # -----------------------
    # Mission execution
    # -----------------------

    def start(self):
        """
            1) Connect to Pixhawk autopilot
            2) Upload mission
            3) Wait for user to begin mission
            4) Monitor take-off
            5) Set plane to LOITER when arrived at camera trap until download complete
            6) Set plane to AUTO if:
                a) timeout event
                b) camera finishes downloading
            7) Monitor landing
        """

        self.connectToAutopilot()

        self.uploadMission(self.__vehicle, self.__data_stations_queue, self.__landing_waypoints)

        # Add listener for vehicle mode change
        self.__vehicle.add_attribute_listener('mode', self.mode_callback)

        # Wait for vehicle to be switched to AUTO mode to begin autonomous mission
        logging.info("Waiting for user to begin mission...")
        while str(self.__vehicle.mode.name) != "AUTO":
            logging.debug("Waiting for user to begin mission...")
            time.sleep(1)

        logging.info("Mission starting...")

        cam_num = len(self.__data_stations)
        land_num = len(self.__landing_waypoints)

        # Monitor takeoff progress
        logging.info("Taking off...")
        while self.__vehicle.commands.next == 1:
            current_altitude = self.__vehicle.location.global_relative_frame.alt
            logging.debug("Current altitude: %s" % current_altitude)
            time.sleep(0.5)

        next_waypoint = self.__vehicle.commands.next

        # Monitor mission progress and engage loiter when each camera trap is reached
        while self.__vehicle.commands.next <= cam_num + 1:

            logging.info("Beginning flight leg to %s..." % (str(next_waypoint)))

            # Pop reference to data station being approached
            current_data_station = self.__data_stations_queue.pop()

            while self.__vehicle.commands.next == next_waypoint: # FIXME: when would this not be the case?

                xbee_ack = self.__xbee.send_command('POWER_ON', iden=current_data_station.iden, timeout=6)
                if xbee_ack:
                    logging.debug("Xbee ACK: %s" % (str(xbee_ack)))

                # data_stations are indexed at 0, and commands are indexed at 1
                # with the first reserved for takeoff. This is why we do [next_waypoint-2]
                distance = self.get_distance_meters(self.__data_stations[next_waypoint - 2],
                                                    self.__vehicle.location.global_frame)

                logging.debug("Distance to camera " + str(next_waypoint) + ": " + str(distance))
                time.sleep(0.5)

            logging.info("Arrived at data station")
            logging.debug("Engaging LOITER mode...")

            # Block until drone is in loiter mode
            while str(self.__vehicle.mode.name) != "LOITER":
                self.__vehicle.mode = VehicleMode("LOITER")
                self.__vehicle.airspeed = self.AIRSPEED_SLOW

            current_data_station.drone_arrived = True

            # Spawn download thread with reference to current_data_station
            download = Download(current_data_station)
            download_thread = threading.Thread(target=download.start())
            download_thread.start()

            download_timer = Timer()
            while True:
                # Cancel download if time elapsed has exceeded predetermined timeout
                if download_timer.time_elapsed() > self.DOWNLOAD_TIMEOUT:
                    current_data_station.timeout = True
                    logging.warn("Download timeout: Download cancelled")
                    break

                if ( (current_data_station.download_complete is False) ):
                    logging.debug("Waiting for data download...")
                else:
                    break

                logging.debug("Time elapsed: %s" % (str(download_timer.time_elapsed())))

                # Give download_thread as much of the computing power as possible to speed up download
                time.sleep(3)

            # Attempt to turn off camera trap
            self.__xbee.send_command('POWER_OFF', iden=current_data_station.iden, timeout=15)
            time.sleep(15)  # wait 15 seconds to turn off camera trap FIXME: Why wait, why not continue only when we know trap is off?

            logging.info("Continuing mission...")

            logging.debug("Engaging AUTO mode...")
            while str(self.__vehicle.mode.name) != "AUTO":
                self.__vehicle.mode = VehicleMode("AUTO")
                self.__vehicle.airspeed = self.AIRSPEED_FAST

            logging.info("Airspeed set to %.2f" % float(self.AIRSPEED_FAST))

            next_waypoint = self.__vehicle.commands.next

        # Return to home
        logging.info("Beginning landing sequence...")

        # Begin stepping through the landing sequence waypoints
        while self.__vehicle.commands.next < (land_num + cam_num):
            distance = self.get_distance_meters(self.__landing_waypoints[next_waypoint - 1],
                                           self.__vehicle.location.global_frame)
            logging.debug("Distance to next landing waypoint %s: %s" % (str(next_waypoint), str(distance)))
            time.sleep(1)

        logging.info("Beginning final approach...")

        current_altitude = self.__vehicle.location.global_relative_frame.alt
        while current_altitude >= 0.5:
            current_altitude = self.__vehicle.location.global_relative_frame.alt
            logging.debug("Altitude: %s" % str(current_altitude))
            time.sleep(0.5)

        logging.info('Mission complete')
        self.isNavigationComplete = True