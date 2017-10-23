"""
Dynamic Navigation Script for Wadi Drone
Daniel Carelli, Mission Mule
"""

import math
import os
import time
from Queue import Empty
from pymavlink import mavutil
from dronekit import connect, VehicleMode, Command

AIRSPEED_SLOW = 15
AIRSPEED_MED = 20
AIRSPEED_FAST = 40

## fn: Callback definition for mode observer
def mode_callback(self, attr_name, msg): # pylint: disable=unused-argument
    """
    This function monitors the vehicle mode. If the vehicle is switched to
    STABALIZE, the raspi relinquishes control.
    """

    # This function needs work. The os._exit is too nuclear, and all logs seem to be lost.

    print "Vehicle Mode", self.mode
    if str(self.mode) == "VehicleMode:STABILIZE": # Quit program entirely to silence Raspberry Pi
        print "Quitting program..."
        filename = "mission_kill.txt"
        target = open(filename, 'w')
        target.write("PROGRAM KILLED")
        os._exit(0) # pylint: disable=protected-access
        print "We should never get here! \nFUCK FUCK FUCK \nAHHHH"
        target.write("We should never get here! \nFUCK FUCK FUCK \nAHHHH")



## CALCULATE DISTANCE BETWEEN TWO GPS COORDINATE
def get_distance_metres(location_1, location_2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.
    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = location_2.lat - location_1.lat
    dlong = location_2.lon - location_1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

## fn: SET UP FULL LOITER AUTOMOATIC MISSION
def set_full_loiter_mission(vehicle, camera_locations, landing_sequence, message_queue):
    """
    Defines the route that the Wadi Drone will take to service the requested camera traps.
    """
    message_queue.put("Download mission")
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()

    message_queue.put("Clear any existing commands")
    cmds.clear()

    #  Add takeoff command
    message_queue.put("Adding takeoff command")
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

    #  Add camera trap locations as unlimeted loiter commands. The aircraft will
    #  fly to the GPS coordinate and circle them indefinitely. The autopilot
    #  proceed to the next mission item after vehicle mode is switched out of
    #  AUTO and back into AUTO.
    message_queue.put("Adding new waypoint commands.")
    for cam in camera_locations:
        print cam
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

    #  Add landing sequence
    message_queue.put("Adding landing sequece")

    #  Start landing Ssquence
    message_queue.put("Adding start landing command")
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
    message_queue.put("Adding runway approach waypoints")
    for i in range(len(landing_sequence)-1):
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
                         landing_sequence[i].lat,
                         landing_sequence[i].lon,
                         int(landing_sequence[i].alt)))

    #  Execute landing operation
    message_queue.put("Adding landing command")
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
                     landing_sequence[len(landing_sequence)-1].lat,
                     landing_sequence[len(landing_sequence)-1].lon,
                     0))

    #  Upload mission
    message_queue.put("Uploading full loiter mission")
    cmds.upload()

## TIMER OBJECT
class Timer(object):
    """
    Timer function that monitors time elapsed when started.
    """
    def __init__(self):
        self.start_timer()

    def start_timer(self):
        """Start the timer"""
        self.start = time.time()

    def time_elapsed(self):
        """Return the time elapsed since the timer was started"""
        return time.time()-self.start

    def time_stamp(self):
        """Create and return a time stamp string for logging purposes"""
        seconds = self.time_elapsed()
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return "%d:%02d:%02d: " % (hours, mins, secs)


################  MAIN FUNCTIONS ################

def navigation(mission_status_queue, camera_locations, landing_sequence, message_queue): # pylint: disable=too-many-branches, too-many-statements
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

    ## CONNECT TO VEHICLE
    connection_string = "/dev/ttyS0"
    print 'Connecting to vehicle on: %s' % connection_string
    vehicle = connect('/dev/ttyS0', baud=57600, wait_ready=True)


    ## WAIT FOR OPERATOR TO INITIATE RASPI MISSION
    while str(vehicle.mode.name) != "GUIDED":
        message_queue.put("Waiting for user to initiate mission")
        time.sleep(0.5)
    message_queue.put("Raspi is taking control of drone")


    ## UPLOAD FULL LOITER MISSION
    set_full_loiter_mission(vehicle, camera_locations, landing_sequence, message_queue)
    vehicle.commands.next = 0


    ## WAIT FOR VEHICLE TO SWITCH TO AUTO
    while str(vehicle.mode.name) != "AUTO":
        message_queue.put("Waiting for user to begin mission")
        time.sleep(1)

    ## ADD MODE CHANGE LISTENER
    vehicle.add_attribute_listener('mode', mode_callback)

    ## MONITOR PROGRESS ON EACH CAMERA LOCATION
    cam_num = len(camera_locations)
    land_num = len(landing_sequence)
    time.sleep(10)

    while vehicle.commands.next == 1:
        current_alt = vehicle.location.global_relative_frame.alt
        message_queue.put("Taking off. Alt: %s" % current_alt)
        time.sleep(0.5)

    nextwaypoint = vehicle.commands.next
    while vehicle.commands.next <= cam_num+1:
        while vehicle.commands.next == nextwaypoint:
            distance = get_distance_metres(camera_locations[nextwaypoint-2],
                                           vehicle.location.global_frame)

            # camera_traps is indexed at 0, and commands are indexed at 1
            # with the first reserved for takeoff. This is why we do [nextwaypoints-2]
            message_queue.put("Distance to camera " + str(nextwaypoint)+ ": " + str(distance))
            time.sleep(0.5)
        message_queue.put("Arrived at camera. Engage LOITER mode.")

        while str(vehicle.mode.name) != "LOITER":
            vehicle.mode = VehicleMode("LOITER")
            vehicle.airspeed = AIRSPEED_SLOW

        #  Toggle Drone_Arrived parameter of camera
        while True:
            try:
                cameras = mission_status_queue.get_nowait()
                cameras[nextwaypoint-2].Drone_Arrived = True
                mission_status_queue.put(cameras)
                break
            except Empty:
                pass

        #  Monitor State of Download
        timer = Timer()
        exit_loop = False
        while True:
            try:
                cameras = mission_status_queue.get_nowait()
                if timer.time_elapsed() > 240:
                    cameras[nextwaypoint-2].Timeout = True
                    message_queue.put("Timeout Event!")

                if ((cameras[nextwaypoint-2].Download_Complete is False) and
                        (cameras[nextwaypoint-2].Timeout is False)):
                    message_queue.put("Waiting for data download")
                else:
                    exit_loop = True
                    mission_status_queue.put(cameras)
                    time.sleep(1)

                if exit_loop:
                    break

            except Empty:
                pass

        message_queue.put("Continuing mission")

        while str(vehicle.mode.name) != "AUTO":
            vehicle.mode = VehicleMode("AUTO")
            vehicle.airspeed = AIRSPEED_FAST

        nextwaypoint = vehicle.commands.next

    ## RETURN TO HOME
    #  At this point, it should begin going through the landing sequence points.
    message_queue.put("Starting Landing Sequence")
    while vehicle.commands.next < (land_num+cam_num):
        distance = get_distance_metres(landing_sequence[nextwaypoint-1],
                                       vehicle.location.global_frame)
        message_queue.put("Distance to Waypoint " + str(nextwaypoint)+ ": " + str(distance))
        time.sleep(1)

    current_alt = vehicle.location.global_relative_frame.alt

    while current_alt >= 0.5:
        current_alt = vehicle.location.global_relative_frame.alt
        message_queue.put("Landing. Alt: %s" % current_alt)
        time.sleep(0.5)
