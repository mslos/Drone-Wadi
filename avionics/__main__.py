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
from services import StatusHandler

def setup_logging():
    """Set up logging [Logging levels in order of seriousness:

    DEBUG < INFO < WARNING < ERROR < CRITICAL
    """

    # Only log when needed
    if os.getenv("DEVELOPMENT") == 'True' or os.getenv("TESTING") == 'True':
        logging_level = logging.DEBUG
    else:
        logging_level = logging.DEBUG

    logging.basicConfig(filename='flight.log',
                        level=logging_level,
                        format='%(asctime)s.%(msecs)03d %(threadName)s %(levelname)s \t%(message)s',
                        datefmt="%d %b %Y %H:%M:%S")

    # Log to STDOUT
    # TODO: only log to stdout in debug mode to speed things up
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s %(threadName)s %(levelname)s \t%(message)s')
    ch.setFormatter(formatter)
    logging.getLogger().addHandler(ch)

def signal_handler(services, threads, signum, frame):
    logging.info("Received signal: SIGINT")

    logging.info("Cleaning up...")

    for service in services:
        service.stop()

    for thread in threads:
        thread.join(2)

    time.sleep(3) # Wait for cleanup

    logging.info("Bye.")

    sys.exit(0)

def main():
    logging.info('\n\n--- mission start ---')

    # Maintains list of active services (serial, data station, heartbeat)
    services = []
    threads = []

    # System status flag set by data station handler
    is_downloading = threading.Event()

    # System status flag set by navigation, monitored by data station handler
    wakeup_event = threading.Event()
    download_event = threading.Event()

    # System status condition set by navigation, alerting data station handler
    # to consume new data station
    new_ds = threading.Event()

    # Maximum 1 data station can download at a time
    rx_queue = queue.Queue()

    # Status to communicate over LED, handled by navigation
    led_status = queue.Queue()

    # Data station communication handling
    # 2 min. connection timeout
    # 2 min. read/write timeout
    # 10 min. download timeout
    dl = DataStationHandler(120000, 120000, 600000, rx_queue)
    services.append(dl)

    nav = Navigation(rx_queue)
    services.append(nav)

    stat = StatusHandler()
    services.append(stat)

    # Gracefully handle SIGINT
    signal.signal(signal.SIGINT, partial(signal_handler, services, threads))
    dl.connect()

    thread_data_station_handler = threading.Thread(target=dl.run, args=(wakeup_event, download_event, new_ds, is_downloading,))
    thread_data_station_handler.daemon = True
    thread_data_station_handler.name = 'DS Handler'
    thread_data_station_handler.start()
    threads.append(thread_data_station_handler)

    thread_navigation = threading.Thread(target=nav.run, args=(wakeup_event, download_event, new_ds, is_downloading, led_status,))
    thread_navigation.daemon = True
    thread_navigation.name = 'Navigation'
    thread_navigation.start()
    threads.append(thread_navigation)

    thread_system_status = threading.Thread(target=stat.run, args=(led_status,))
    thread_system_status.daemon = True
    thread_system_status.name = 'LED Handler'
    thread_system_status.start()
    threads.append(thread_system_status)

    # Ugly, I know. Python2.7 doesn't play nice with elegant SIGINT handling
    # if a call to the thread's join method has already been made so we have
    # to do this until pymavlink finally supports Python3.
    while True:
        time.sleep(5)

    # Wait for daemon threads to return on their own
    thread_data_station_handler.join()
    thread_navigation.join()
    thread_system_status.join()

if __name__ == "__main__":
    setup_logging()
    main()
