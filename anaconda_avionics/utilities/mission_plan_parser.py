"""
This module takes in a vehicle object, reads in the mission and returns a list
of Camera objects and LandingWaypoint objects that are later used to upload and
monitor data mule missions.
"""

from anaconda_avionics.utilities import DataStation
from anaconda_avionics.utilities import LandingWaypoint


# TODO: reconfigure this to accept Pixhawk mission plan and execute accordingly
class MissionPlanParser(object):

    self._autopilot = None
    self._data_stations = []
    self._landing_waypoints = []

    def __init__(self, _autopilot):
        self._autopilot = _autopilot

    def extract_waypoints(self):
        """
        Downloads the MAVlink commadns from the pixhawk and reurns a list of
        Camera and LandingWaypoint objects
        """

        # Read in list of MAVlink commands from the pixhakw.

        # Identify which commands correspond to data stations and which
        # correspond to the landing sequence by checking Parameter #1 of each
        # command.

        # Return the results
        return self._data_stations, self._landing_waypoints
