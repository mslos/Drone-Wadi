########################################################
## Data retrieval script for Wadi Drone
## Daniel Carelli, Mission Mule
## Summer 2017
########################################################

from plane_navigation_script0 import navigation, log
from image_download_script_multiple import download_sequence
import argparse
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
import threading
from Queue import Queue
from mission_logger import log, mission_logger

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

## fn: GET CAMERA TRAP INFORMATION
def extract_waypoints(message_queue):

    parser = argparse.ArgumentParser(description='Process some.')
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
    args = parser.parse_args()

    log(message_queue, "Reading Mission File")
    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    cameras = [[i for i in line.strip().split(',')] for line in args.file[0].readlines()]

    #  Raw latitude, longitude, and altitude for CAMERA TRAPS translated to
    #  Camera objects
    camera_traps = []
    for line in range(len(cameras)):
    	if not cameras[line][0].isalpha(): # Not data column descriptor
            new_camera = Camera(float(cameras[line][0]),float(cameras[line][1]),int(cameras[line][2]), cameras[line][3])
            log(message_queue, new_camera.summary())
            camera_traps.append(new_camera)

    #  Make list of LocationGlobal Objects for camera traps and Camera IDs
    camera_locations = []
    camera_IDs = []
    for cam in camera_traps:
        camera_locations.append(cam.getLocationObject())
        camera_IDs.append(cam.ID)

    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    log(message_queue, "Reading Landing Sequence")
    landing = [[i for i in line.strip().split(',')] for line in args.file[1].readlines()]

    #  Raw latitude, longitude, and altitude for LANDING SEQUENCE translated to
    #  LocationGlobals
    landing_waypoints = []
    for line in range(len(landing)):
    	if not landing[line][0].isalpha(): # Not data column descriptor
            landing_waypoints.append(LocationGlobal(float(landing[line][0]),float(landing[line][1]),float(landing[line][2])))
            log(message_queue, "Lon: " + str(landing[line][0]) + " Lat: " + str(landing[line][1]) + " Alt: " + str(landing[line][2]))

    return camera_traps, camera_locations, landing_waypoints, camera_IDs

###############################################################################

## PREPARE MISSION LOG
message_queue = Queue()
logging_thread = threading.Thread(target=mission_logger, args=(message_queue,))
logging_thread.start()

## EXTRACT WAYPOINTS FROM CSV FILES
camera_traps, camera_locations, landing_waypoints, camera_IDs = extract_waypoints(message_queue)

## CREATE QUEUE ACCESSIBLE TO BOTH THREADS
q = Queue()
q.put(camera_traps)

## CREATE AND START NAVIGATION AND DOWNLOAD THREADS
navigation_thread = threading.Thread(target=navigation, args=(q,camera_locations,landing_waypoints,message_queue,))
download_thread = threading.Thread(target=download_sequence, args=(q, camera_IDs,))

navigation_thread.start()
download_thread.start()

navigation_thread.join()

## GET FINAL STATUS ON CAMERA TRAPS AND DISPLAY
camera_traps = q.get()

for camera in camera_traps:
    log(message_queue, camera.summary())
