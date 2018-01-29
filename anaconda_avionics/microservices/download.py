import logging
import time

from anaconda_avionics.utilities import SFTPClient
from anaconda_avionics.utilities import Timer

class Download(object):

    CONNECTION_TIMEOUT_SECONDS = 30

    __sftp = None
    __data_station = None

    is_connected = False

    def __init__(self, _data_station):

        self.__data_station = _data_station # Reference to DataStation object monitored by Navigation

        # TODO: change this to dynamically distribute required certificate
        self.__sftp = SFTPClient('pi', 'raspberry', str(self.__data_station.identity))



        # # After connection made
        # self.start()

    def connect(self):
        # Establish connection with camera trap
        data_station_connection_timer = Timer()
        while True:
            try:
                if data_station_connection_timer.time_elapsed() > self.CONNECTION_TIMEOUT_SECONDS:
                    logging.error("Connection to data station %s failed permanently" % (self.__data_station.identity))
                    break

                self.__sftp.connect()
                self.is_connected = True
                break

            except Exception as e:
                logging.warn(e)

            time.sleep(1)

    def start(self):
        """
        For desired camera trap:
            1) Download field data and data station logs to drone
            2) Delete successfully transferred field data and logs from data station
        """
        logging.debug("Beginning download...")
        self.__data_station.download_started = True

        # Prioritizes field data transfer over log data
        self.__sftp.downloadAllFieldData()
        self.__sftp.downloadAllLogData()

        logging.info("Download complete")

        logging.debug("Beginning removal of successfully transferred files...")

        # Removes only files that are successfully transferred to vehicle
        # TODO: uncomment this out when system is more stable
        # self.__sftp.deleteAllFieldData()
        # self.__sftp.deleteAllLogData()

        logging.info("Removal of successfully transferred files complete")

        # Close connection to data station
        self.__sftp.close()

        # Mark download as complete so Navigation service knows to continue mission
        self.__data_station.download_complete = True