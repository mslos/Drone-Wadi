import logging
import argparse

from anaconda_avionics import Mission
from anaconda_avionics.utilities import MissionPlanParser

# TODO: parse waypoints here and pass to mission to keep mission waypoint agnostic
# TODO: long-term -- automatically start and wait for mission upload from QGroundControl

def main():
    # Set up logging [Logging levels in order of seriousness: DEBUG < INFO < WARNING < ERROR < CRITICAL]
    logging.basicConfig(filename='flight-log.log',
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
                        datefmt="%d %b %Y %H:%M:%S")

    logging.info('Logging started')


    # Begin extraction of waypoints from CSV file
    logging.debug("Beginning waypoint extraction...")

    # Get argument input from mission start
    parser = argparse.ArgumentParser(description='Extract CSV waypoint file paths for data stations and ')
    parser.add_argument('file', type=argparse.FileType('r'), nargs='+')
    args = parser.parse_args()

    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    data_station_waypoints = [[i for i in line.strip().split(',')] for line in args.file[0].readlines()]

    #  Read absolute GPS coordinates and altitude from CSV file into list of lists
    landing_waypoints = [[i for i in line.strip().split(',')] for line in args.file[1].readlines()]

    data_station_waypoints, landing_waypoints = \
        MissionPlanParser(data_station_waypoints, landing_waypoints).extract_waypoints()

    logging.debug("Waypoint extraction complete")

    # Initialize and start mission
    m = Mission(data_station_waypoints, landing_waypoints)

    m.log_data_station_status()
    m.start()


if __name__ == "__main__":
    main()