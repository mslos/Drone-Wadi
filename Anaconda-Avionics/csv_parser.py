"""
This module takes in a CSV file in the command line and returns a list of Camera objects
and LandingWaypoint objects that are later used to upload and monitor data mule missions.
Eventually, this will accept MavLink commands instead-of/in-conjuction-with the CSV file.
"""

import argparse
from dronekit import LocationGlobalRelative

class Camera(LocationGlobalRelative): # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """
    Class that stores information relevant to navigation for each camera trap
    """

    def __init__(self, longitude, latitude, altitude, iden):
        super(Camera).__init__()
        self.lon = longitude
        self.lat = latitude
        self.alt = altitude
        self.iden = iden
        self.timeout = False
        self.drone_arrived = False
        self.download_started = False
        self.download_complete = False

    def summary(self):
        """
        Returns a summary (string) of the status of the camera.
        """

        ret_string = "Camera ID: " + self.iden + "\n"
        ret_string += "    Lon: %s Lat: %s Alt: %s\n" % (self.lon, self.lat, self.alt)
        ret_string += "    Timeout:           %s\n" % self.timeout
        ret_string += "    Drone_Arrived:     %s\n" % self.drone_arrived
        ret_string += "    Download_Started:  %s\n" % self.download_started
        ret_string += "    Download_Complete: %s\n" % self.download_complete
        return ret_string

class LandingWaypoint(LocationGlobalRelative): # pylint: disable=too-few-public-methods
    """
    Class that stores information relevant to navigation used for the landing approach.
    """

    def __init__(self, number, longitude, latitude, altitude, airspeed="N/A"): # pylint: disable=too-many-arguments
        super(LandingWaypoint).__init__()
        self.waypoint_number = number
        self.lon = longitude
        self.lat = latitude
        self.alt = altitude
        self.airspeed = airspeed

    def summary(self):
        """
        Returns a summary (string) of the waypoint.
        """

        ret_string = "Landing Waypoint Number: " + self.waypoint_number + "\n"
        ret_string += "    Lon: %s Lat: %s Alt: %s\n" % (self.lon, self.lat, self.alt)
        ret_string += "    Airspeed (m/s):           %s\n" % self.airspeed
        return ret_string

## fn: GET CAMERA TRAP INFORMATION
def extract_waypoints():
    """
    Reads CSV file and returns list of LandingWaypoint objects and list of Camera objects.
    """

    parser = argparse.ArgumentParser(description='Process some.')
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
    args = parser.parse_args()

    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    cameras = [[i for i in line.strip().split(',')] for line in args.file[0].readlines()]

    #  Raw latitude, longitude, and altitude for CAMERA TRAPS translated to
    #  Camera objects
    number_of_cameras = len(cameras)
    camera_traps = []
    for line in range(number_of_cameras):
        if not cameras[line][0].isalpha(): # Not data column descriptor
            new_camera = Camera(
                float(cameras[line][0]),
                float(cameras[line][1]),
                int(cameras[line][2]),
                cameras[line][3])
            camera_traps.append(new_camera)

    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    landing = [[i for i in line.strip().split(',')] for line in args.file[1].readlines()]

    #  Raw latitude, longitude, and altitude for LANDING SEQUENCE translated to
    #  LandingWaypoints
    landing_waypoints = []
    waypoint_num = 0
    number_of_waypoints = len(landing)
    for line in range(number_of_waypoints):
        if not landing[line][0].isalpha(): # Not data column descriptor
            waypoint_num += 1
            new_landing_waypoint = LandingWaypoint(
                waypoint_num,
                float(landing[line][0]),
                float(landing[line][1]),
                float(landing[line][2]))
            landing_waypoints.append(new_landing_waypoint)

    return camera_traps, landing_waypoints
