import json
import socket
import time
import os


from ftplib import FTP

class DroneClient:

    __client = None         # Pseudo-private FTP client
    __download_path = None  # Relative path to write downloaded photos into

    def __init__(self, login_credentials_path, server_ip_address):

        # Move into correct directory for file path references
        os.chdir(os.path.dirname(__file__))

        self.__download_path = './photos/'

        # Get server login credentials
        with open(login_credentials_path) as config:
            login = json.load(config)

        # Make directory to download to if one does not exist
        if not (os.path.isdir(self.__download_path)):
            os.mkdir(self.__download_path)

        self.__client = FTP('')

        # If server is refusing to connect (it isn't up yet),
        # keep trying until connection is made
        while True:
            try:
                self.__client.connect(server_ip_address, 2121) # Try to connect
                break
            except socket.error: # Connection refused
                time.sleep(1) # Try again in one second

        self.__client.login(login['username'], login['password'])
        self.__client.cwd('.')

    def getFileList(self):
        return self.__client.nlst()

    def downloadFile(self, file_name):
        # Create new file in downloads directory with same file name
        local_file = open(self.__download_path+file_name, 'wb')

        # Download the file in 1024 byte chunks so buffer does not overflow
        self.__client.retrbinary('RETR ' + file_name, local_file.write, 1024)

        local_file.close()

    def downloadAllPhotos(self):
        for file_name in self.getFileList():
            self.downloadFile(file_name)

    def quit(self):
        self.__client.quit()
