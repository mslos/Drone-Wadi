import socket
import traceback
import logging

import paramiko
import os

# TODO: handle poor connection timeouts
# TODO: add robust logging for flight records
# TODO: add certificate-based connection with certificate paired to camera-trap prior to deployment

class SFTPClient(object):

    __sftp = None                       # Our SFTP client
    __transport = None                  # Paramiko transport
    __remote_path = './data/'           # Location relative to SFTP root directory where the data files are located; current SFTP root from pi@cameratrap.local /home/pi/
    __local_destination = './data/'     # Where downloaded files will be kept
    __hostname = None
    __username = None
    __password = None

    def __init__(self, _username, _password, _hostname):

        # Move into correct directory for file path references
        os.chdir(os.path.dirname(__file__))

        # Paramiko client configuration
        UseGSSAPI = False  # enable GSS-API / SSPI authentication
        DoGSSAPIKeyExchange = False
        Port = 22   # Standard SSH port

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
        logging.info("Connecting to data station %s..." % (self.__hostname))

        try:
            self.__transport = paramiko.Transport((self.__hostname, Port))
            self.__transport.connect(hostkey, self.__username, self.__password, gss_host=socket.getfqdn(self.__hostname),
                      gss_auth=UseGSSAPI, gss_kex=DoGSSAPIKeyExchange)
            self.__sftp = paramiko.SFTPClient.from_transport(self.__transport)

            logging.info("Connection established to data station: %s" % (self.__hostname))

            try:
                self.__sftp.mkdir(self.__remote_path)
            except IOError:
                logging.debug('{0} directory already exists'.format(self.__remote_path))

        except Exception as e:
            logging.warn('Connection failed. Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()
            self.close()


    def getFileList(self):
        return self.__sftp.listdir(self.__remote_path)

    def downloadFile(self, file_name):
        logging.info("Downloading file: %s" % (file_name))
        try:
            self.__sftp.get(self.__remote_path+file_name, self.__local_destination+file_name)
        except IOError as e:
            logging.error(e)

    def deleteFile(self, file_name):
        logging.info("Deleting file from camera trap: %s" % (file_name))
        try:
            self.__sftp.remove(self.__remote_path+file_name)
        except IOError as e:
            logging.error(e)

    # TODO: allow for more finely-grained deletion
    def downloadAndDeleteAllFiles(self):
        file_list = self.getFileList()
        if not file_list:
            logging.info("No files to download")
        else:

            logging.info("Downloading %i files..." % (len(file_list)))
            # Download all files
            for file_name in file_list:
                self.downloadFile(file_name)

            # TODO: go through files now on drone and only delete those from camera trap
            # Remove successfully downloaded files
            for file_name in file_list:
                self.deleteFile(file_name)

    def close(self):
        logging.info("Closing connection to SFTP server... [hostname: %s]" % (self.__hostname))

        self.__sftp.close()

        # TODO: let drone know that download is done here; time to continue mission
        logging.info("Connection to SFTP server closed [hostname: %s]" % (self.__hostname))