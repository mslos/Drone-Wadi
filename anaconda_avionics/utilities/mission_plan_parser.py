"""
This module takes in a vehicle object, reads in the mission and returns a list
of Camera objects and LandingWaypoint objects that are later used to upload and
monitor data mule missions.
"""

#from anaconda_avionics.utilities.
from data_station import DataStation
#from anaconda_avionics.utilities.
from landing_waypoint import LandingWaypoint

class MissionPlanParser(object):

    def __init__(self, _autopilot):
        self._autopilot = _autopilot
        self._data_stations = []
        self._landing_waypoints = []

        # load the commands
        self._cmds  = self._autopilot.commands
        self._cmds.download()
        self._cmds.wait_ready()
        self._number_of_commands = self._cmds.count

    def extract_waypoints(self):
        """
        Downloads the MAVlink commadns from the pixhawk and reurns a list of
        Camera and LandingWaypoint objects
        """

        # Read in list of MAVlink commands from the pixhakw.
        cmd_index = 1
        # command 0 is always Mission Start
        # command 1 is always Takeoff
        while (cmd_index < self._number_of_commands):
        # TODO: distinguish between landing, takeoff and obstacle avoidance

            # get the command ID


            cmd = self._autopilot._wploader.wp(cmd_index)
            print cmd.command
            # determine if the command indicates a data station
            if (cmd.command == 16): # 16 corresponds to MAV_CMD_NAV_WAYPOINT
                new_waypoint = LandingWaypoint(cmd_index, cmd.x, cmd.y, cmd.z)
                self._landing_waypoints.append(new_waypoint)

            elif (cmd.command == 189): # 189 corresponds to DO_LAND_START
                new_waypoint = LandingWaypoint(cmd_index, cmd.x, cmd.y, cmd.z)
                self._landing_waypoints.append(new_waypoint)

            elif (cmd.command == 12): # 21 corresponds to MAV_CMD_NAV_LAND
                new_waypoint = LandingWaypoint(cmd_index, cmd.x, cmd.y, cmd.z)
                self._landing_waypoints.append(new_waypoint)

            elif (cmd.command == 31): # 31 corresponds to MAV_CMD_NAV_LOITER_TO_ALT	
                new_waypoint = LandingWaypoint(cmd_index, cmd.x, cmd.y, cmd.z)
                self._landing_waypoints.append(new_waypoint)

            elif (cmd.command == 201): # corresponds to a data station! MAV_CMD_DO_SET_ROI
                new_data_station = DataStation(cmd.x, cmd.y, cmd.z, cmd.param4)
                self._data_stations.append(new_data_station)
                # the next waypoint is MAV_CMD_NAV_WAYPOINT
                # at the same location
                # TODO: add check to make sure the above is true
                cmd_index += 1

            else:
                # we should throw some king of global error for cmds that
                # the drone is not expecting
                pass

            cmd_index += 1

        # Return the results
        return self._data_stations, self._landing_waypoints

if __name__ == '__main__':
    from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command

    connection_string = raw_input("Enter connection string: ")
    print 'Connecting to vehicle on: %s' % connection_string
    vehicle = connect(connection_string, baud=57600, wait_ready=True)
    print 'Connection succesful!'

    parser = MissionPlanParser(vehicle)
    parser.extract_waypoints()

    print "Landing Waypoints: "
    for waypoint in parser._landing_waypoints:
        print "Lat: ", waypoint.lat, "Lon: ", waypoint.lon, "Alt: ", waypoint.alt

    print "\n----------------------\n"

    for ds in parser._data_stations:
        print "Data Station: ", ds.identity
        print "    Lat: ", ds.lat, "Lon: ", ds.lon, "Alt: ", ds.alt
        print "    Timeout Event: ", ds.timeout
        print "    Drone Arrived: ", ds.drone_arrived
        print "    Download Start: ", ds.download_started
        print "    Download Complete: ", ds.download_complete
