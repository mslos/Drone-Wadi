"""
Unit tests to verify partial functionality of data mule system.
"""

import threading
from Queue import Queue

import anaconda_avionics.plane_navigation_script
from anaconda_avionics.utilities import csv_parser
from anaconda_avionics.utilities import Logger
from xbee_comm import Xbee


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

    anaconda_avionics.plane_navigation_script.prepare_mission(mission_queue, landing_waypoints, message_queue)

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

    anaconda_avionics.plane_navigation_script.navigation(mission_queue, landing_waypoints, message_queue)

def unit_test_xbee_comm(iden_num):
    """
    This unit test has two funtions:
     * if iden = '?', then it will query the camera trap for its ID and print
       this value
     * otherwise, the xBee will turn on and off a camera trap of given ID
    """
    dummy_queue = Queue()
    xbee = Xbee(dummy_queue)

    if iden_num == '?':
        response = xbee.send_command('Identify')
        print "Camera ID: %s" % response[0]

    else:
        xbee.send_command('Power On', iden=iden_num, timeout=30)
        time.sleep(30)
        xbee.send_command('Power Off', iden=iden_num, timeout=30)
