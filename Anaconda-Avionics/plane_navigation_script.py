########################################################
## Dynamic Navigation Script for Wadi Drone
## Daniel Carelli, Mission Mule
## Summer 2017
########################################################

from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
import time
import math
from pymavlink import mavutil
import sys
import os
from Queue import Queue, Empty

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
def set_full_loiter_mission(vehicle, camera_locations, landing_sequence, message_queue):
    message_queue.put("Download mission")
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()

    message_queue.put("Clear any existing commands")
    cmds.clear()

    #  Add takeoff command
    message_queue.put("Adding takeoff command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 30, 0, 0, 0, 0, 0, 30))

    #  Add camera trap locations as unlimeted loiter commands. The aircraft will
    #  fly to the GPS coordinate and circle them indefinitely. The autopilot
    #  proceed to the next mission item after vehicle mode is switched out of
    #  AUTO and back into AUTO.
    message_queue.put("Adding new waypoint commands.")
    for cam in camera_locations:
        print cam
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, cam.lat, cam.lon, cam.alt))

    #  Add landing sequence
    message_queue.put("Adding landing sequece")

    #  Start landing Ssquence
    message_queue.put("Adding start landing command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_DO_LAND_START, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    #  Approach runway
    message_queue.put("Adding runway approach waypoints")
    for i in range(len(landing_sequence)-1):
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, landing_sequence[i].lat, landing_sequence[i].lon, int(landing_sequence[i].alt)))

    #  Execute landing operation
    message_queue.put("Adding landing command")
    cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, landing_sequence[len(landing_sequence)-1].lat, landing_sequence[len(landing_sequence)-1].lon, 0))

    #  Upload mission
    message_queue.put("Uploading full loiter mission")
    cmds.upload()

## TIMER OBJECT
class Timer():
    def __init__(self):
        self.start = time.time()
    def start_timer(self):
        self.start = time.time()
    def timeElapsed(self):
        return (time.time()-self.start)
    def timeStamp(self):
	seconds = self.timeElapsed()
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return ("%d:%02d:%02d: " % (h, m, s))


################  MAIN FUNCTIONS ################

def navigation(q, camera_locations, landing_sequence, message_queue):
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
    
    while (vehicle.commands.next == 1):
    	current_alt = vehicle.location.global_relative_frame.alt
    	message_queue.put("Taking off. Alt: %s" % current_alt)
    	time.sleep(0.5)

    nextwaypoint = vehicle.commands.next
    while (vehicle.commands.next <= cam_num+1):
    	while vehicle.commands.next == nextwaypoint:
    		distance = get_distance_metres(camera_locations[nextwaypoint-2], vehicle.location.global_frame)
    		# camera_traps is indexed at 0, and commands are indexed at 1
    		# with the first reserved for takeoff. This is why we do [nextwaypoints-2]
    		message_queue.put("Distance to camera " + str(nextwaypoint)+ ": " + str(distance))
    		time.sleep(0.5)
    	message_queue.put("Arrived at camera. LOITER for 30 seonds.")

    	while (str(vehicle.mode.name) != "LOITER"):
    		vehicle.mode = VehicleMode("LOITER")

        #  Toggle Drone_Arrived parameter of camera
        while True:
		try:
            		cameras = q.get_nowait()
                	cameras[nextwaypoint-2].Drone_Arrived = True
                	q.put(cameras)
                	break
		except Empty:
			pass

        #  Monitor State of Download
        timer = Timer()
        exit_loop = False
        while True:
		try:
            		cameras = q.get_nowait()
                	if (timer.timeElapsed() > 240):
                    		cameras[nextwaypoint-2].Timeout = True
                    		message_queue.put("Timeout Event!")
                	if ((cameras[nextwaypoint-2].Download_Complete == False) and (cameras[nextwaypoint-2].Timeout == False)):
                	    	message_queue.put("Waiting for data download")
                	else:
                    		exit_loop = True
                	q.put(cameras)
                	time.sleep(1)
            		if exit_loop:
                		break
		except Empty:
			pass

    	message_queue.put("Continuing mission")

    	while (str(vehicle.mode.name) != "AUTO"):
    		vehicle.mode = VehicleMode("AUTO")
    	nextwaypoint = vehicle.commands.next

    ## RETURN TO HOME
    #  At this point, it should begin going through the landing sequence points.
    message_queue.put("Starting Landing Sequence")
    while (vehicle.commands.next < (land_num+cam_num)):
    	distance = get_distance_metres(landing_sequence[nextwaypoint-1], vehicle.location.global_frame)
    	message_queue.put("Distance to Waypoint " + str(nextwaypoint)+ ": " + str(distance))
    	time.sleep(1)

    current_alt = vehicle.location.global_relative_frame.alt

    while (current_alt >= 0.5):
    	current_alt = vehicle.location.global_relative_frame.alt
    	message_queue.put("Landing. Alt: %s" % current_alt)
    	time.sleep(0.5)