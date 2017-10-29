"""
This is the main navigation script for a data mule mission. This program spawns three threads:
    1) navigation thread for directing the airplane to each camera locations
    2) image_download_script to manage the data tranfer from camera trap to drone
    3) logger to keep track of mission logs for post flight analysis
"""

import threading
from Queue import Queue, Empty
from plane_navigation_script import navigation
from image_download_script_multiple import download_sequence
from utilities import Logger
import csv_parser

###############################################################################

def data_mule_mission():
    """
    Function for starting a data retrieveal mission for Wadi Drone
    """

    message_queue = Queue()
    logger = Logger("date", "time", message_queue)

    ## EXTRACT WAYPOINTS FROM CSV FILES
    camera_traps, landing_waypoints = csv_parser.extract_waypoints()

    ## need to remove this -- change image download scrip to accept camera objects
    camera_idens = []
    for cam in camera_traps:
        camera_idens.append(cam.iden)

    ## CREATE QUEUE ACCESSIBLE TO BOTH THREADS
    mission_queue = Queue()
    mission_queue.put(camera_traps)

    ## CREATE AND START NAVIGATION AND DOWNLOAD THREADS
    navigation_thread = threading.Thread(target=navigation, args=(mission_queue,
                                                                  landing_waypoints,
                                                                  message_queue,))

    download_thread = threading.Thread(target=download_sequence, args=(mission_queue,
                                                                       camera_idens,
                                                                       message_queue,))

    logger_thread = threading.Thread(target=logger.start_logging, args=())

    navigation_thread.start()
    download_thread.start()
    logger_thread.start()

    ## GET FINAL STATUS ON CAMERA TRAPS AND DISPLAY
    while True:
        try:
            camera_traps = mission_queue.get_nowait()
            break
        except Empty:
            pass

    logger.single_entry("Camera Trap Summary \n")

    for camera in camera_traps:
        log_message = '\n'+ camera.summary()
        logger.single_entry(log_message)

if __name__ == "__main__":
    data_mule_mission()
