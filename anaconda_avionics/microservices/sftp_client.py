import socket
import traceback

import paramiko
import os

# TODO: handle poor connection timeouts
# TODO: add robust logging for flight records
# TODO: add certificate-based connection with certificate paired to camera-trap prior to deployment

class SFTPClient:

    __sftp = None                       # Our SFTP client
    __transport = None                  # Paramiko transport
    __remote_path = './data/'           # Location relative to SFTP root directory where the data files are located
    __local_destination = './data/'     # Where downloaded files will be kept

    def __init__(self, _username, _password, _hostname):

        # Move into correct directory for file path references
        os.chdir(os.path.dirname(__file__))

        # paramiko.util.log_to_file('demo_sftp.log')    # set up logging

        # Paramiko client configuration
        UseGSSAPI = False  # enable GSS-API / SSPI authentication
        DoGSSAPIKeyExchange = False
        Port = 22   # Standard SSH port

        # TODO: change from password to public key cryptography
        # Login credentials
        username = _username
        password = _password
        hostname = _hostname

        # get host key, if we know one
        hostkeytype = None
        hostkey = None

        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))

        if hostname in host_keys:
            hostkeytype = host_keys[hostname].keys()[0]
            hostkey = host_keys[hostname][hostkeytype]

        # now, connect and use paramiko Transport to negotiate SSH2 across the connection
        try:
            self.__transport = paramiko.Transport((hostname, Port))
            self.__transport.connect(hostkey, username, password, gss_host=socket.getfqdn(hostname),
                      gss_auth=UseGSSAPI, gss_kex=DoGSSAPIKeyExchange)
            self.__sftp = paramiko.SFTPClient.from_transport(self.__transport)

            try:
                self.__sftp.mkdir(self.__remote_path)
            except IOError:
                print(self.__remote_path + ' directory already exists')

        except Exception as e:
            print('Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()
            self.close()


    def getFileList(self):
        return self.__sftp.listdir(self.__remote_path)

    def downloadFile(self, file_name):
        print "Downloading file: " + file_name # TODO: Log this
        try:
            self.__sftp.get(self.__remote_path+file_name, self.__local_destination+file_name)
        except IOError as e:
            print e

    def deleteFile(self, file_name):
        print "Deleting file from camera trap: " + file_name # TODO: Log this
        try:
            self.__sftp.remove(self.__remote_path+file_name)
        except IOError as e:
            print e

    def downloadAllFiles(self):
        file_list = self.getFileList()
        if not file_list:
            print "No files to download." #TODO: log here
        else:
            # Download all files
            for file_name in file_list:
                self.downloadFile(file_name)

            # Remove successfully downloaded files
            for file_name in file_list:
                self.deleteFile(file_name)

    def close(self):
        print "Closing connection..."

        self.__sftp.close()

        # TODO: let drone know that download is done here; time to continue mission
        print "Connection closed. Continuing mission."