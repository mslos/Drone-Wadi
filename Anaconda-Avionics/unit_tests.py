"""
Unit tests to verify partial functionality of data mule system.
"""

from Queue import Queue
import threading
import plane_navigation_script
import csv_parser
from utilities import Logger

def unit_test_csv_parser():
    """
    This unit test only extracts camera trap locations and landing
    sequence data and converts them into the appropriate objects.
    """
    camera_traps, landing_waypoints = csv_parser.extract_waypoints()

    for camera in camera_traps:
        print camera.summary()

    for waypoint in landing_waypoints:
        print waypoint.summary()

def unit_test_prepare_mission():
    """
    This unit test stops after uploading the mission to the pixhawk.
    """
    camera_traps, landing_waypoints = csv_parser.extract_waypoints()
    mission_queue = Queue()
    mission_queue.put(camera_traps)

    message_queue = Queue()
    logger = Logger('Unit Test:', 'prepare_mission', message_queue)

    logger_thread = threading.Thread(target=logger.start_logging, args=())
    logger_thread.start()

    plane_navigation_script.prepare_mission(mission_queue, landing_waypoints, message_queue)

    message_queue.put('mission_end')

def unit_test_navigation():
    """
    This unit test runs throught a full data mule mission without actually
    trying to download data from camer traps.
    """
    camera_traps, landing_waypoints = csv_parser.extract_waypoints()
    mission_queue = Queue()
    mission_queue.put(camera_traps)

    message_queue = Queue()
    logger = Logger('Unit Test:', 'prepare_mission', message_queue)

    logger_thread = threading.Thread(target=logger.start_logging, args=())
    logger_thread.start()

    plane_navigation_script.navigation(mission_queue, landing_waypoints, message_queue)
