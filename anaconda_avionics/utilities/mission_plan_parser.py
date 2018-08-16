"""
This module takes in a CSV file in the command line and returns a list of Camera objects
and LandingWaypoint objects that are later used to upload and monitor data mule missions.
Eventually, this will accept MavLink commands instead-of/in-conjuction-with the CSV file.
"""

from anaconda_avionics.utilities import DataStation
from anaconda_avionics.utilities import LandingWaypoint


# TODO: reconfigure this to accept QGroundControl mission plan and execute accordingly
class MissionPlanParser(object):

    __data_waypoints = None     # Waypoints to be loitered over
    __landing_waypoints = None  # Waypoints to be flown through in landing sequence

    def __init__(self, _data_waypoints, _landing_waypoints):
        self.__data_waypoints = _data_waypoints
        self.__landing_waypoints = _landing_waypoints

    def extract_waypoints(self):
        """
        Reads CSV file and returns list of LandingWaypoint objects and list of Camera objects.
        """

        #  Raw latitude, longitude, and altitude for CAMERA TRAPS translated to
        #  Camera objects
        number_of_data_stations = len(self.__data_waypoints)
        data_stations = []
        for line in range(number_of_data_stations):
            if not self.__data_waypoints[line][0].isalpha(): # Not data column descriptor
                new_data_station = DataStation( # TODO: change Camera object to "DataStation"
                    float(self.__data_waypoints[line][0]),
                    float(self.__data_waypoints[line][1]),
                    int(self.__data_waypoints[line][2]),
                    str(self.__data_waypoints[line][3]))
                data_stations.append(new_data_station)

        #  Raw latitude, longitude, and altitude for LANDING SEQUENCE translated to
        #  LandingWaypoints
        landing_waypoints = []
        waypoint_num = 0
        number_of_waypoints = len(self.__landing_waypoints)
        for line in range(number_of_waypoints):
            if not self.__landing_waypoints[line][0].isalpha(): # Not data column descriptor
                waypoint_num += 1
                new_landing_waypoint = LandingWaypoint(
                    waypoint_num,
                    float(self.__landing_waypoints[line][0]),
                    float(self.__landing_waypoints[line][1]),
                    float(self.__landing_waypoints[line][2]))
                landing_waypoints.append(new_landing_waypoint)

        return data_stations, landing_waypoints
