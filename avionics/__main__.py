import logging
import os
import serial
import signal
import sys
import time
import threading
import queue

from functools import partial

from services import DataStationHandler
from services import Navigation

def setup_logging():
    """Set up logging [Logging levels in order of seriousness:

    DEBUG < INFO < WARNING < ERROR < CRITICAL
    """

    # Only log when needed
    if os.getenv("DEVELOPMENT") == 'True' or os.getenv("TESTING") == 'True':
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(filename='flight.log',
                        level=logging_level,
                        format='%(asctime)s.%(msecs)03d %(levelname)s \t%(message)s',
                        datefmt="%d %b %Y %H:%M:%S")

    # Log to STDOUT
    # TODO: only log to stdout in debug mode to speed things up
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s \t%(message)s')
    ch.setFormatter(formatter)
    logging.getLogger().addHandler(ch)

def signal_handler(services, signum, frame):
    logging.info("Received signal: %s" % signal.getsignal(signum))

    logging.info("Cleaning up...")

    for service in services:
        service.stop()

    time.sleep(3) # Wait for cleanup

    logging.info("Bye.")

    exit()

def main():
    logging.info('\n\n--- mission start ---')

    # Maintains list of active services (serial, data station, heartbeat)
    services = []

    # System status flag set by data station handler, monitored by heartbeat
    is_downloading = threading.Event()

    # Maximum 50 data stations in a mission
    rx_queue = queue.Queue(maxsize=50)
    rx_lock = threading.Lock()

    # Data station communication handling
    # 2 min. connection timeout
    # 2 min. read/write timeout
    # 10 min. download timeout
    dl = DataStationHandler(120000, 120000, 600000, rx_queue)
    services.append(dl)

    nav = Navigation(rx_queue)
    services.append(nav)

    # Gracefully handle SIGINT
    signal.signal(signal.SIGINT, partial(signal_handler, services))
    dl.connect()

    thread_data_station_handler = threading.Thread(target=dl.run, args=(rx_lock, is_downloading,))
    thread_data_station_handler.daemon = True
    thread_data_station_handler.name = 'Data Station Communication Handler'
    thread_data_station_handler.start()

    thread_navigation = threading.Thread(target=nav.run, args=(is_downloading,))
    thread_navigation.daemon = True
    thread_navigation.name = 'Navigation'
    thread_navigation.start()

    # Wait for daemon threads to return on their own
    thread_data_station_handler.join()
    thread_navigation.join()

if __name__ == "__main__":
    setup_logging()
    main()
