"""
This test will confirm the functionality of the system starting from QGS upload
to drone download and parsing. The flow of the test will be as follows:
    1) Load the unit test data station in Mission Mule's QGroundControl.
    2) Load the unit test landing sequance in Mission Mule's QGroundControl.
    3) Auto-Generate the mission and upload to the drone.
    4) From the anaconda_avionics directory, run
                    python -m test_mission_plan_parser
"""

from utilities.mission_plan_parser import MissionPlanParser
from utilities.data_station import DataStation
from utilities.landing_waypoint import LandingWaypoint
from dronekit import connect

connection_string = "/dev/ttyS0"



if __name__ == '__main__':

    # create the expected values
    expected_data_stations = []
    expected_data_stations.append(DataStation(24.521592, 54.435452, 60, '03'))
    expected_data_stations.append(DataStation(24.522882, 54.437273, 60, '07'))
    expected_data_stations.append(DataStation(24.526051, 54.432802, 60, '17'))
    expected_landing_waypoints = []
    expected_landing_waypoints.append(LandingWaypoint(24.527945, 54.430411, 50))
    expected_landing_waypoints.append(LandingWaypoint(24.527945, 54.430411, 50))
    expected_landing_waypoints.append(LandingWaypoint(24.523096, 54.433605, 50))


    # connect to vehicle
    vehicle = connect(connection_string, baud=57600, wait_ready=True)

    # instatiate MissionPlanParser object
    mission_plan_parser = MissionPlanParser(vehicle)

    # extract waypoints
    data_stations, landing_waypoints = mission_plan_parser.extract_waypoints()

    data_stations_test_passed = True
    for i in range(3):
        data_stations_test_passed &= expected_data_stations[i].lat = data_stations[i].lat
        data_stations_test_passed &= expected_data_stations[i].lon = data_stations[i].lon
        data_stations_test_passed &= expected_data_stations[i].alt = data_stations[i].alt
        data_stations_test_passed &= expected_data_stations[i].id = data_stations[i].id

    landing_sequence_test_passed = True
    for i in range(3):
        landing_sequence_test_passed &= expected_landing_waypoints[i].lat = landing_waypoints[i].lat
        landing_sequence_test_passed &= expected_landing_waypoints[i].lon = landing_waypoints[i].lon
        landing_sequence_test_passed &= expected_landing_waypoints[i].alt = landing_waypoints[i].alt

    print "Data Station Test Passed: ", data_stations_test_passed
    print "Landing Sequence Test Passed: ", landing_sequence_test_passed
