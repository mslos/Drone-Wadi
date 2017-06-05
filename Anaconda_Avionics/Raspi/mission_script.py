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
import serial
import subprocess as sp
import threading

class Command ():
    def __init__(self,ID,command,value):
        self.id = ID
        self.command = command
        self.value = value
    def makeCommand (self):
        if self.value == "":
            message = ":"+self.command+"0"+"\r\n" #Added space here
        else:
            message = ":"+self.command+" "+self.value+"\r\n"
        return message
    def writeCommand (self):
        ser.write(self.makeCommand())

class Response():
    def __init__(self,ID,command,value):
        self.rawMessage = ser.readlines()
        self.id = ID
        self.command = command
        self.value = value
    def excludeGarbage(self):
        notGarbage = []
        returnMessage = self.rawMessage
        for i in returnMessage:
            if "%" in i:
                message = ""
                read = False
                for c in range(len(i)):
                    if i[c] == "%":
                        read = True
                    if i[c] == "\r" or i[c] == "\n":
                        read = False
                    if read:
                        message += i[c]
                notGarbage.append(message)
        return notGarbage
#    def checkSum(self):
#        message = self.excludeGarbage()
#        for i in message:
#            if len(i)!=
    def readMessage(self):
        messageDictList = []
        messages = self.excludeGarbage()
        for i in messages:
            messageList = i.replace("%","").split(" ")
            messageDict = {}
            messageDict ["ID"] = messageList [0]
            messageDict ["command"] = messageList [1]
            messageDict ["value"] = messageList [2]
            messageDictList.append(messageDict)
        return messageDictList
    def checkEcho(self): #Check if the response matches the commmand
        messageDictList = self.readMessage()
        print(messageDictList)
        for i in messageDictList:
            messageDictList.remove(i)
            if self.command == i ["command"] and self.value in i["value"] and self.id == i ["ID"]:
                return messageDictList
        return "retry"
    def realResponse(self): #Dummy, Optimization (?)
        message = self.checkEcho()
        if message:
            return message
        else:
            return None

def downloadFiles(): #Transfers files from camera trap to drone.
# Rsync Arguments:
#   -a       is equivalent to -rlptgoD, preserves everything recursion enabled
#   -v       verbose
#   -P       combines --partial (keeps partially transferred files) and --pro-
#            gress (shows progress of transfer)
#   --chmod  sets permissions; "a"-for all:user/owner, group owner and all other users;
#            "rwx" is read, write, execute rights
#   --update This forces rsync to skip any files for which the destination file already
#            exists and has a date later than the source file.
# Camera IP: 192.168.10.22
    copy_files = sp.call("rsync -avP --chmod=a=rwX --update pi@192.168.42.15:/media/usbhdd/DCIM/ /media/usbhddDrone", shell=True)
    # make_backup = sp.call("ssh -v pi@192.168.10.22 'python -v /home/pi/Desktop/camerabu.py'",shell=True)


def POWR (value):
    message = Command(ID,"POWR",value)
    message.writeCommand()
    response = Response(ID,"POWR",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        ser.readlines()
        return POWR(value)
    return responseMessage

def IDEN (value="0"):
    message = Command(ID,"IDEN",value)
    message.writeCommand()
    response = Response(ID,"IDEN",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        return IDEN()
    return responseMessage

def RSET (value="0"):
    message = Command(ID,"RSET",value)
    message.writeCommand()
    response = Response(ID,"RSET",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        return RSET()
    return responseMessage


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
        retString += "    Lon: " + str(self.longitude) + " Lat: " + str(self.latitude) + " Alt: " + str(self.altitude) + "\n"
        retString += "    Timeout:           " + str(self.Timeout) + "\n"
        retString += "    Drone_Arrived:     " + str(self.Drone_Arrived) + "\n"
        retString += "    Download_Started:  " + str(self.Download_Started) + "\n"
        retString += "    Download_Complete: " + str(self.Download_Complete) + "\n"
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
def set_full_loiter_mission(vehicle):
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
        print cam
        cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, cam.longitude, cam.latitude, cam.altitude))

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

## TIMER OBJECT
class Timer():
    def __init__():
        self.start = time.time()
    def start():
        self.start = time.time()
    def timeElapsed():
        return (self.start - time.time())

################  MAIN FUNCTIONS ################
def download_sequence():
    ser = serial.Serial("/dev/ttyUSB0", 9600, timeout = 1)
    for cam in camera_traps:
        ID = cam.ID
        os.system("sudo mount /dev/sda1") #mounts USB flash drive into which photos are saved

        ID = IDEN()[0]["ID"]
        #os.system("sudo python /home/pi/Desktop/GreenLED.py")
        POWR ("1")
        #os.system("sudo python /home/pi/Desktop/BlueLED.py")
        state = POWR ("?")
        while state[0]["value"] != "000001":
            state = POWR("?")
        #os.system("sudo python /home/pi/Desktop/RedLED.py")
        downloadFiles()
        POWR ("0")
        #os.system("sudo python /home/pi/Desktop/CyanLED.py")
        state = POWR ("?")
        print(state)
        while state[0] ["value"] != "000000":
            state = POWR ("?")
        RSET()
        os.system("sudo umount /dev/sda1") #unmounts USB
        #os.system("sudo python /home/pi/Desktop/RedLED.py")

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
    set_full_loiter_mission(vehicle)
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
    		distance = get_distance_metres(camera_traps[nextwaypoint-2].getLocationObject(), vehicle.location.global_frame)
    		# camera_traps is indexed at 0, and commands are indexed at 1
    		# with the first reserved for takeoff. This is why we do [nextwaypoints-2]
    		log(target, "Distance to camera " + str(nextwaypoint)+ ": " + str(distance))
    		time.sleep(0.5)

        #  Switch out of AUTO and into LOITER to downlaod data from camera trap
    	log(target, "Arrived at camera.")
    	while (str(vehicle.mode.name) != "LOITER"):
    		vehicle.mode = VehicleMode("LOITER")
        camera_traps[nextwaypoint-2].Drone_Arrived = True

        #  Start timer and monitor download progress before moving to next waypoint
        t_loiter = Timer()
        while ((camera_traps[nextwaypoint-2].Download_Complete == False) and (camera_traps[nextwaypoint-2].Timeout == False)):
            log(target, "Drone is waiting for data download.")
            if (t_loiter.timeElapsed() >= 240): # 4 minute Timeout
                log(target, "Timeout event!")
                camera_traps[nextwaypoint-2].Timeout = True

        #  Switch out of LOITER and into AUTO to conitinue to next mission waypoint
    	log(target, "Moving to next waypoint.")
    	while (str(vehicle.mode.name) != "AUTO"):
    		vehicle.mode = VehicleMode("AUTO")

        #  Update next waypoint
    	nextwaypoint = vehicle.commands.next

    ## RETURN TO HOME
    #  At this point, it should begin going through the landing sequence points.
    log(target, "Starting Landing Sequence")
    while (vehicle.commands.next < (land_num+cam_num)):
    	distance = get_distance_metres(landing_sequence[nextwaypoint-1], vehicle.location.global_frame)
    	log(target, "Distance to Waypoint " + str(nextwaypoint)+ ": " + str(distance))
    	time.sleep(1)

    current_alt = vehicle.location.global_relative_frame.alt

    while (current_alt >= 0.5):
    	current_alt = vehicle.location.global_relative_frame.alt
    	log(target, "Landing. Alt: %s" % current_alt)
    	time.sleep(0.5)

################  MAIN FUNCTIONS ################
if __name__ == "__main__":
    ## PREPARE MISSION LOG FILE
    filename = "mission_raspi_log.txt"
    target = open(filename, 'w')

    ## EXTRACT WAYPOINTS AND LANDING SEQUNCE
    camera_traps, landing_sequence = extract_waypoints()

    ## START MISSION THREADS
    navigation_thread = threading.Thread(target=navigation, args=())
    download_thread = threading.Thread(target=download_sequence, args=())

    navigation_thread.start()
    download_thread.start()

    navigation_thread.join()
    download_thread.join()

    for cam in camera_traps:
        log(target, cam.summary())
