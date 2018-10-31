import logging
import os
import queue
import random
import time
import threading

from .timer import Timer
from .download import Download
from .xbee import XBee

class DataStationHandler(object):
    """Communication handler for data stations (XBee station wakeup and SFTP download)

    This class manages downstream interfacing between payload and data
    station.

    SFTP Download:
        Each download is spawned as a worker thread to isolate the effect
        of failure in case of unexpected socket exceptions.

    XBee Wakeup:
        When the UAV arrives at a data station, the station is woken up with
        an XBee RF signal including its data station ID ('redwood', 'streetcat', etc.)

    """

    def __init__(self, _connection_timeout_millis, _read_write_timeout_millis,
        _overall_timeout_millis, _rx_queue):

        self.connection_timeout_millis = _connection_timeout_millis
        self.read_write_timeout_millis = _read_write_timeout_millis
        self.overall_timeout_millis = _overall_timeout_millis
        self.rx_queue = _rx_queue
        self.xbee = XBee()
        self._alive = True

    def connect(self):
        self.xbee.connect()

    def run(self, wakeup_event, download_event, new_ds, is_downloading, is_awake):
        """Loop forever and handle downloads as data stations are reached"""

        while self._alive:
            # Wait until there's something in the download queue
            logging.debug("Waiting for data station...")
            new_ds.wait()

            logging.debug("New data station in queue, beginning wakeup and download...")

            # Do the thing
            is_downloading.set()
            self._wake_download_and_sleep(wakeup_event, download_event, is_downloading, is_awake)
            new_ds.clear()
            is_downloading.clear()

        logging.error("Data station handler terminated")

    def stop(self):
        logging.info("Stopping data station handler...")
        self._alive = False

    def _wake_download_and_sleep(self, wakeup_event, download_event, is_downloading, is_awake):

        # Get data station ID as message from rx_queue
        data_station_id = self.rx_queue.get().strip() # Removes invisible characters

        logging.info('Data station arrival: %s', data_station_id)

        # Wait for navigation to give the wakeup goahead
        wakeup_event.wait()

        # Wake up data station
        logging.info('Waking up over XBee...')
        self.xbee.send_command(data_station_id, 'POWER_ON')

        xbee_wake_command_timer = Timer()
        wakeup_successful = True
        if not (os.getenv('TESTING') == 'True'):
            while not self.xbee.acknowledge(data_station_id, 'POWER_ON'):
                logging.debug("POWER_ON data station %s", data_station_id)
                self.xbee.send_command(data_station_id, 'POWER_ON')
                time.sleep(0.5) # Try again in 0.5s

                # Will try waking up data station over XBee for minimum 4 min before moving on
                if download_event.is_set() and xbee_wake_command_timer.time_elapsed() > 240:
                    wakeup_successful = False
                    logging.error("POWER_ON command ACK failure. Moving on...")
                    break

        is_awake.set()
        download_event.wait()

        # Don't actually download
        if (os.getenv('TESTING') == 'True' or os.getenv('DEVELOPMENT') == 'True'):
            r = random.randint(10,20)

            logging.debug('Simulating download for %i seconds', r)
            time.sleep(r) # "Download" for random time between 10 and 20 seconds

        # Only try download if wakeup was successful
        elif (wakeup_successful): # This is the real world (ahhh!)

            logging.info('XBee ACK received, beginning download...')

            # '.local' ensures visibility on the network
            download_worker = Download(data_station_id.strip()+'.local',
                                       self.connection_timeout_millis)

            try:
                # This throws an error if the connection times out
                download_worker.start()

                # Attempt to join the thread after timeout.
                download_worker.join(self.overall_timeout_millis/1000)

                # If still alive, we know that the download timed out.
                if download_worker.is_alive():
                    logging.info("Download timeout: Download cancelled")
                else:
                    logging.info("Download complete")

            except Exception as e:
                logging.error(e)

        # Wake up data station
        logging.info('Shutting down data station %s...', data_station_id)
        self.xbee.send_command(data_station_id, 'POWER_OFF')

        xbee_sleep_command_timer = Timer()
        # If the data station actually turned on and we're not in test mode, shut it down
        if not ((os.getenv('TESTING') == 'True') or os.getenv('DEVELOPMENT') == 'True') and \
            (wakeup_successful == True):
            while not self.xbee.acknowledge(data_station_id, 'POWER_OFF'):
                logging.debug("POWER_OFF data station %s", data_station_id)
                self.xbee.send_command(data_station_id, 'POWER_OFF')
                time.sleep(0.5) # Try again in 0.5s

                # Will try shutting down data station over XBee for 20 seconds before moving on
                if xbee_sleep_command_timer.time_elapsed() > 20:
                    logging.error("POWER_OFF command ACK failure")
                    break

        is_awake.clear()

        # Mark task as complete, even if it fails
        self.rx_queue.task_done()

        logging.debug("Moving on...")
