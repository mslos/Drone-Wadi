import socket
import traceback
import logging

import paramiko
import os

# TODO: handle poor connection timeouts
# TODO: add robust logging for flight records
# TODO: add certificate-based connection with certificate paired to camera-trap prior to deployment

class SFTPClient(object):

    REMOTE_FIELD_DATA_SOURCE = './data/field/'        # Location relative to SFTP root directory where the field data files are located; current SFTP root from pi@cameratrap.local /home/pi/
    LOCAL_FIELD_DATA_DESTINATION = './data/field/'  # Where downloaded data station field data will be kept

    REMOTE_LOG_SOURCE = './data/logs/'                # Location relative to SFTP root directory where the data station log files are located
    LOCAL_LOG_DESTINATION = './data/logs/'          # Where downloaded data station logs will be kept

    __sftp = None                                       # Our SFTP client
    __transport = None                                  # Paramiko transport

    __hostname = None
    __username = None
    __password = None

    def __init__(self, _username, _password, _hostname):

        # Paramiko client configuration
        UseGSSAPI = False  # enable GSS-API / SSPI authentication
        DoGSSAPIKeyExchange = False
        Port = 22   # Standard SSH port

        # Update destination directories to include hostname for data differentiation
        self.LOCAL_FIELD_DATA_DESTINATION = './data/field/%s/' % (_hostname)
        self.LOCAL_LOG_DESTINATION = './data/logs/%s/' % (_hostname)

        # TODO: change from password to public key cryptography
        # Login credentials
        self.__username = _username
        self.__password = _password
        self.__hostname = _hostname


        # get host key, if we know one
        hostkeytype = None
        hostkey = None

        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))

        if self.__hostname in host_keys:
            hostkeytype = host_keys[self.__hostname].keys()[0]
            hostkey = host_keys[self.__hostname][hostkeytype]

        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        logging.info("Connecting to data station... [hostname: %s]" % (self.__hostname))

        try:
            self.__transport = paramiko.Transport((self.__hostname, Port))
            self.__transport.connect(hostkey, self.__username, self.__password, gss_host=socket.getfqdn(self.__hostname),
                      gss_auth=UseGSSAPI, gss_kex=DoGSSAPIKeyExchange)
            self.__sftp = paramiko.SFTPClient.from_transport(self.__transport)

            logging.info("Connection established to data station: %s" % (self.__hostname))

            # Ensure remote field data directory exists
            try:
                self.__sftp.mkdir(self.REMOTE_FIELD_DATA_SOURCE)
            except IOError:
                logging.debug('{0} remote field data directory already exists'.format(self.REMOTE_FIELD_DATA_SOURCE))

            # Ensure remote log directory exists
            try:
                self.__sftp.mkdir(self.REMOTE_LOG_SOURCE)
            except IOError:
                logging.debug('{0} remote log directory already exists'.format(self.REMOTE_LOG_SOURCE))

            # Ensure local field data directory exists
            if not os.path.exists(self.LOCAL_FIELD_DATA_DESTINATION):
                os.makedirs(self.LOCAL_FIELD_DATA_DESTINATION)

            # Ensure local log data directory exists
            if not os.path.exists(self.LOCAL_LOG_DESTINATION):
                os.makedirs(self.LOCAL_LOG_DESTINATION)

        except Exception as e:
            logging.warn('Connection failed.')
            logging.debug('%s: %s' % (e.__class__, e))
            # traceback.print_exc()


    # -----------------------
    # General utility methods
    # -----------------------

    def getRemoteFileList(self, remote_path):
        return self.__sftp.listdir(remote_path)

    def downloadFile(self, remote_path, local_destination, file_name):
        """
        Download remote file to given local destination
        """
        logging.info("Downloading file: %s" % (file_name))
        try:
            self.__sftp.get(remote_path+file_name, local_destination+file_name)
        except IOError as e:
            logging.error(e)

    def deleteFile(self, remote_path, file_name):
        """
        Delete file from given path on remote data station
        """
        logging.info("Deleting file from camera trap: %s" % (file_name))
        try:
            self.__sftp.remove(remote_path+file_name)
        except IOError as e:
            logging.error(e)

    # NOTICE: Make sure to close the SFTP connection after download is complete
    def close(self):
        logging.debug("Closing connection to data station... [hostname: %s]" % (self.__hostname))
        self.__sftp.close()
        logging.info("Connection to data station closed [hostname: %s]" % (self.__hostname))


    # -----------------------
    # Field data methods
    # -----------------------

    def downloadAllFieldData(self):
        """
        Download all data station field data
        """
        file_list = self.getRemoteFileList(self.REMOTE_FIELD_DATA_SOURCE)
        if not file_list:
            logging.info("No field data files to download")
        else:
            logging.info("Downloading %i field data files..." % (len(file_list)))
            # Download all files
            for file_name in file_list:
                self.downloadFile(self.REMOTE_FIELD_DATA_SOURCE, self.LOCAL_FIELD_DATA_DESTINATION, file_name)

    def deleteAllFieldData(self):
        """
        Delete all log data that has successfully been downloaded
        """
        logging.debug("Beginning data station log removal")
        for file_name in os.listdir(self.LOCAL_FIELD_DATA_DESTINATION):
            self.deleteFile(self.REMOTE_FIELD_DATA_SOURCE, file_name)
        logging.info("Field data removal complete")


    # -----------------------
    # Log data methods
    # -----------------------

    def downloadAllLogData(self):
        """
        Download all data station log data
        """
        file_list = self.getRemoteFileList(self.REMOTE_LOG_SOURCE)
        if not file_list:
            logging.info("No log files to download")
        else:
            logging.info("Downloading %i log files..." % (len(file_list)))
            # Download all files
            for file_name in file_list:
                self.downloadFile(self.REMOTE_LOG_SOURCE, self.LOCAL_LOG_DESTINATION, file_name)

    def deleteAllLogData(self):
        """
        Remove successfully downloaded log files
        """
        logging.debug("Beginning data station log removal")
        for file_name in os.listdir(self.LOCAL_LOG_DESTINATION): # List newly downloaded files
            self.deleteFile(self.REMOTE_LOG_SOURCE, file_name)
        logging.info("Field data removal complete")