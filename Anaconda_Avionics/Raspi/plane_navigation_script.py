########################################################
## Basic Mission to test waypoints, landing and takeoff
## Daniel Carelli, Mission Mule
## Summer 2017
########################################################

from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
import time
import math
from pymavlink import mavutil
import argparse
import sys
import os


class Camera:
    def __init__(self, longitude, latitude, altitude, ID):
        self.longitude = longitude
        self.latitude = latitude
        self.altitude = altitude
        self.ID = ID
        self.Timeout = False
        self.Drone_Arrived = False
        self.Download_Started = False
        self.Download_Complete = False

    def getLocationObject(self):
        return LocationGlobal(self.longitude, self.latitude, self.altitude)

    def summary(self):
        retString = "Camera ID: " + self.ID + "\n"
        retString += "    Lat: " + str(self.latitude) + " Lon: " + str(self.longitude) + " Alt: " + str(self.altitude) + "\n"
        retString += "    Timeout:           " + str(self.Timeout) + "\n"
        retString += "    Drone_Arrived:     " + str(self.Drone_Arrived) + "\n"
        retString += "    Download_Started:  " + str(self.Download_Started) + "\n"
        retString += "    Download_Complete: " + str(self.Download_Complete) + "\n" + "\n"
        return retString

## fn: Callback definition for mode observer
def mode_callback(self, attr_name, msg):
	print "Vehicle Mode", self.mode
	if str(self.mode) == "VehicleMode:STABILIZE": # Quit program entirely to silence Raspberry Pi
		print "Quitting program..."
		filename = "mission_kill.txt"
		target = open(filename, 'w')
		target.write("PROGRAM KILLED")
		os._exit(0)
		print "We should never get here! \nFUCK FUCK FUCK \nAHHHH"
		target.write("We should never get here! \nFUCK FUCK FUCK \nAHHHH")

## fn: GET CAMERA TRAP INFORMATION
def extract_waypoints():
    ## PREPARE MISSION LOG FILE
    filename = "mission_raspi_log.txt"
    target = open(filename, 'w')

    parser = argparse.ArgumentParser(description='Process some.')
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
    args = parser.parse_args()

    log(target, "Reading Mission File")
    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    cameras = [[i for i in line.strip().split(',')] for line in args.file[0].readlines()]

    #  Raw latitude, longitude, and altitude for CAMERA TRAPS translated to
    #  Camera objects
    camera_traps = []
    for line in range(len(cameras)):
    	if not cameras[line][0].isalpha(): # Not data column descriptor
            new_camera = Camera(float(cameras[line][0]),float(cameras[line][1]),int(cameras[line][2]), cameras[line][3])
            log(target, new_camera.summary())
            camera_traps.append(new_camera)

    log(target, "Reading Landing Sequence")
    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    landing = [[i for i in line.strip().split(',')] for line in args.file[1].readlines()]

    #  Raw latitude, longitude, and altitude for LANDING SEQUENCE translated to
    #  LocationGlobals
    landing_waypoints = []
    for line in range(len(landing)):
    	if not landing[line][0].isalpha(): # Not data column descriptor
            landing_waypoints.append(LocationGlobal(float(landing[line][0]),float(landing[line][1]),float(landing[line][2])))
            log(target, "Lon: " + str(landing[line][0]) + " Lat: " + str(landing[line][1]) + " Alt: " + str(landing[line][2]))

    target.close()
    return camera_traps, landing_waypoints

## CALCULATE DISTANCE BETWEEN TWO GPS COORDINATE
def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.
    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

## fn: SET UP FULL LOITER AUTOMOATIC MISSION
def set_full_loiter_mission(vehicle, camera_traps, landing_sequence):
    log(target, "Download mission")
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()

    log(target, "Clear any existing commands")
    cmds.clear()

    #  Add takeoff command
    log(target, "Adding takeoff command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 30, 0, 0, 0, 0, 0, 30))

    #  Add camera trap locations as unlimeted loiter commands. The aircraft will
    #  fly to the GPS coordinate and circle them indefinitely. The autopilot
    #  proceed to the next mission item after vehicle mode is switched out of
    #  AUTO and back into AUTO.
    log(target, "Adding new waypoint commands.")
    for cam in camera_traps:
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, cam.latitude, cam.longitude, cam.altitude))

    #  Add landing sequence
    log(target, "Adding landing sequece")

    #  Start landing Ssquence
    log(target, "Adding start landing command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_DO_LAND_START, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    #  Approach runway
    log(target, "Adding runway approach waypoints")
    for i in range(len(landing_sequence)-1):
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, landing_sequence[i].lat, landing_sequence[i].lon, int(landing_sequence[i].alt)))

    #  Execute landing operation
    log(target, "Adding landing command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, landing_sequence[len(landing_sequence)-1].lat, landing_sequence[len(landing_sequence)-1].lon, 0))

    #  Upload mission
    log(target, "Uploading full loiter mission")
    cmds.upload()

## fn: LOG STATUS PROCESSOR
def log(target_file, message):
	print message
	target_file.write(message)
	target_file.write('\n')

################  MAIN FUNCTIONS ################

def navigation():
    ## CONNECT TO VEHICLE
    connection_string = "/dev/ttyS0"
    print 'Connecting to vehicle on: %s' % connection_string
    vehicle = connect('/dev/ttyS0', baud=57600, wait_ready=True)

    ## WAIT FOR OPERATOR TO INITIATE RASPI MISSION
    while str(vehicle.mode.name) != "GUIDED":
    	log(target, "Waiting for user to initiate mission")
    	time.sleep(0.5)
    print log(target, "Raspi is taking control of drone")

    ## UPLOAD FULL LOITER MISSION
    set_full_loiter_mission(vehicle, camera_locations, landing_sequence)
    vehicle.commands.next = 0

    ## WAIT FOR VEHICLE TO SWITCH TO AUTO
    while str(vehicle.mode.name) != "AUTO":
        log(target, "Waiting for user to begin mission")
        time.sleep(1)

    ## ADD MODE CHANGE LISTENER
    vehicle.add_attribute_listener('mode', mode_callback)

    ## MONITOR PROGRESS ON EACH CAMERA LOCATION
    cam_num = len(camera_traps)
    land_num = len(landing_sequence)

    while (vehicle.commands.next == 1):
    	current_alt = vehicle.location.global_relative_frame.alt
    	log(target, "Taking off. Alt: %s" % current_alt)
    	time.sleep(0.5)

    nextwaypoint = vehicle.commands.next
    while (vehicle.commands.next <= cam_num+1):
    	while vehicle.commands.next == nextwaypoint:
    		distance = get_distance_metres(camera_locations[nextwaypoint-2], vehicle.location.global_frame)
    		# camera_locations is indexed at 0, and commands are indexed at 1
    		# with the first reserved for takeoff. This is why we do [nextwaypoints-2]
    		log(target, "Distance to camera " + str(nextwaypoint)+ ": " + str(distance))
    		time.sleep(0.5)
    	log(target, "Arrived at camera. LOITER for 30 seonds.")
    	#  This is how we change vehicle mode
    	while (str(vehicle.mode.name) != "LOITER"):
    		vehicle.mode = VehicleMode("LOITER")
    	time.sleep(30)
    	log(target, "Download complete. Continue mission")
    	while (str(vehicle.mode.name) != "AUTO"):
    		vehicle.mode = VehicleMode("AUTO")
    	nextwaypoint = vehicle.commands.next

    ## RETURN TO HOME
    #  At this point, it should begin going through the landing sequence points.
    log(target, "Starting Landing Sequence")
    while (vehicle.commands.next < (land_num+cam_num)):
    	distance = get_distance_metres(camera_locations[nextwaypoint-1], vehicle.location.global_frame)
    	log(target, "Distance to Waypoint " + str(nextwaypoint)+ ": " + str(distance))
    	time.sleep(1)

    current_alt = vehicle.location.global_relative_frame.alt

    while (current_alt >= 0.5):
    	current_alt = vehicle.location.global_relative_frame.alt
    	log(target, "Landing. Alt: %s" % current_alt)
    	time.sleep(0.5)

################  MAIN FUNCTIONS ################
## PREPARE MISSION LOG FILE
filename = "mission_raspi_log.txt"
target = open(filename, 'w')

## EXTRACT WAYPOINTS AND LANDING SEQUNCE
camera_traps, landing_sequence = extract_waypoints()
camera_locations = []
for cam in camera_traps:
    camera_locations.append(cam.getLocationObject)

navigation()
