import logging

from anaconda_avionics.utilities import SFTPClient

class Download(object):

    __sftp = None
    __data_station = None

    def __init__(self, _data_station):

        self.__data_station = _data_station # Reference to DataStation object monitored by Navigation

        # TODO: change this to dynamically distribute required certificate
        self.__sftp = SFTPClient('pi', 'raspberry', self.__data_station.iden)


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
        self.__sftp.deleteAllFieldData()
        self.__sftp.deleteAllLogData()

        logging.info("Removal of successfully transferred files complete")

        self.__data_station.download_complete = True

        # Close connection to data station
        self.__sftp.close()