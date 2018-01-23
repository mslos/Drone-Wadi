import math
import os
import time
import logging

from pymavlink import mavutil
from dronekit import connect, VehicleMode, Command
from Queue import Empty

from anaconda_avionics.utilities import Timer

class Navigation(object):


    AIRSPEED_SLOW = 15
    AIRSPEED_MED = 20
    AIRSPEED_FAST = 40
    DOWNLOAD_TIMEOUT = 240

    __mode = None
    __cameras = None
    __vehicle = None

    __mission_queue = None
    __landing_waypoints = None
    __message_queue = None

    def __init__(self, _mission_queue, _landing_waypoints):
        self.__mission_queue = _mission_queue
        self.__landing_waypoints = _landing_waypoints

    def start(self):
        """
            Main navigation function:
                1) Connect to Pixhawk
                2) Upload mission
                3) Monitor take-off
                4) Set plane to LOITER when arrived at camera trap
                5) Set plane to AUTO if:
                    a) timeout event
                    b) camera finishes downloading
                6) Monitor landing
            """

        ## CONNECT TO VEHICLE AND UPLOAD MISSION
        self.__cameras, self.__vehicle = self.prepare_mission(self.__mission_queue, self.__landing_waypoints)

        cam_num = len(self.__cameras)
        land_num = len(self.__landing_waypoints)

        ## WAIT FOR VEHICLE TO SWITCH TO AUTO
        while str(self.__vehicle.mode.name) != "AUTO":
            logging.info("Waiting for user to begin mission")
            time.sleep(1)

        ## ADD MODE CHANGE LISTENER
        self.__vehicle.add_attribute_listener('mode', self.mode_callback)

        ## MONITOR PROGRESS ON EACH CAMERA LOCATION
        while self.__vehicle.commands.next == 1:
            current_alt = self.__vehicle.location.global_relative_frame.alt
            logging.info("Taking off. Altitude: %s" % current_alt)
            time.sleep(0.5) # FIXME: why sleep here?

        nextwaypoint = self.__vehicle.commands.next
        while self.__vehicle.commands.next <= cam_num + 1:
            while self.__vehicle.commands.next == nextwaypoint:
                distance = self.get_distance_metres(cameras[nextwaypoint - 2],
                                               self.__vehicle.location.global_frame)

                # camera_traps is indexed at 0, and commands are indexed at 1
                # with the first reserved for takeoff. This is why we do [nextwaypoints-2]
                logging.info("Distance to camera " + str(nextwaypoint) + ": " + str(distance))
                time.sleep(0.5)

            logging.info("Arrived at camera. Engaging LOITER mode.")

            while str(self.__vehicle.mode.name) != "LOITER":
                self.__vehicle.mode = VehicleMode("LOITER")
                self.__vehicle.airspeed = self.AIRSPEED_SLOW

            # Toggle Drone_Arrived parameter of camera
            while True:
                try:
                    cameras = self.__mission_queue.get_nowait()
                    cameras[nextwaypoint - 2].drone_arrived = True
                    self.__mission_queue.put(cameras)
                    break
                except Empty:
                    pass

            # Monitor State of Download
            timer = Timer()
            while True:
                try:
                    cameras = self.__mission_queue.get_nowait()
                    if timer.time_elapsed() > self.DOWNLOAD_TIMEOUT:
                        cameras[nextwaypoint - 2].timeout = True
                        logging.warn("Download timeout")

                    self.__mission_queue.put(cameras)
                    # TODO: clean up and comment this section
                    if ((cameras[nextwaypoint - 2].download_complete is False) and
                            (cameras[nextwaypoint - 2].timeout is False)):
                        logging.info("Waiting for data download...")
                    else:
                        break

                    time.sleep(1) # FIXME: Why sleep?

                except Empty:
                    pass

            time.sleep(15)  # wait 15 seconds to turn off camera trap FIXME: Why wait, why not continue when we know trap is off?
            logging.info("Continuing mission...")

            while str(self.__vehicle.mode.name) != "AUTO":
                self.__vehicle.mode = VehicleMode("AUTO")
                self.__vehicle.airspeed = self.AIRSPEED_FAST

            logging.info("Switched vehicle to AUTO mode")
            logging.info("Airspeed set to AIRSPEED_FAST")

            nextwaypoint = self.__vehicle.commands.next

        ## RETURN TO HOME
        #  At this point, it should begin going through the landing sequence points.
        logging.info("Starting landing sequence...")
        while self.__vehicle.commands.next < (land_num + cam_num):
            distance = self.get_distance_meters(self.__landing_waypoints[nextwaypoint - 1],
                                           self.__vehicle.location.global_frame)
            logging.info("Distance to waypoint " + str(nextwaypoint) + ": " + str(distance))
            time.sleep(1)

        current_alt = self.__vehicle.location.global_relative_frame.alt

        while current_alt >= 0.5:
            current_alt = self.__vehicle.location.global_relative_frame.alt
            logging.info("Landing. Alt: %s" % current_alt)
            time.sleep(0.5)

        logging.info('Mission complete')

    # TODO: rework for less nuclear option--no os.exit(0)
    def mode_callback(self, attr_name, msg):
        """
            This function monitors the vehicle mode. If the vehicle is switched to STABALIZE, the companion computer
            (Raspberry Pi) immediately relinquishes control to drone operator for manual operation.
        """
        logging.info(str(self.__mode))

        if str(self.__mode) == "VehicleMode:STABILIZE":  # Quit program entirely to silence Raspberry Pi
            logging.warn("Vehicle mode switched to STABILIZE. Killing program.")
            os._exit(0)  # pylint: disable=protected-access
            logging.critical("We should never get here! FUCK FUCK FUCK AHHHH")

    # Calculate distance between two GPS coordinates
    # TODO: There must be a better way to do this...
    def get_distance_meters(self, location_1, location_2):
        """
           Returns the ground distance in metres between two LocationGlobal objects.
           This method is an approximation, and will not be accurate over large distances and close to the
           earth's poles. It comes from the ArduPilot test code:
           https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
           """
        dlat = location_2.lat - location_1.lat
        dlong = location_2.lon - location_1.lon
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

    ## fn: SET UP FULL LOITER AUTOMATIC MISSION
    def set_full_loiter_mission(self, vehicle, cameras, landing_waypoints, message_queue):
        """
        Defines the route that the Wadi Drone will take to service the requested camera traps.
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

        #  Start landing Ssquence
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
            message_queue.put('New Waypoint:\n%s' % waypoint.summary())
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

    def prepare_mission(self, mission_queue, landing_waypoints):
        """
        Connect to the Pixhawk and upload the mission.
        """

        while True:
            try:
                cameras = mission_queue.get_nowait()
                mission_queue.put(cameras)
                break
            except Empty:
                pass

        ## CONNECT TO VEHICLE
        connection_string = "/dev/ttyS0"
        logging.info('Connecting to vehicle on: %s' % connection_string)
        vehicle = connect('/dev/ttyS0', baud=57600, wait_ready=True)

        ## UPLOAD FULL LOITER MISSION
        self.set_full_loiter_mission(vehicle, cameras, landing_waypoints)
        vehicle.commands.next = 0

        return cameras, vehicle
