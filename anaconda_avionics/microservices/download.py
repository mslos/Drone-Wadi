import logging

from anaconda_avionics.utilities import Xbee
from anaconda_avionics.utilities import SFTPClient
from anaconda_avionics.utilities import Timeout

class Download(object):

    __sftp = None
    __xbee = None
    __cameras = None
    __camera_traps = None

    def __init__(self, camera_traps, message_queue):

        self.__cameras = camera_traps.get_nowait()
        self.__camera_traps = camera_traps  # Camera traps queue reference

        self.__camera_traps.put(self.__cameras)

        # Create and connect to xBee module
        self.__xbee = Xbee(message_queue)

    def start(self):
        # For desired camera trap: turn on camera trap, download to drone, delete photos from camera trap, turn off camera trap

        for i in range(len(self.__cameras)):

            # Broadcast a directed "POWER_ON" Command to the desired camera trap
            while True:
                xbee_ack = self.__xbee.send_command('POWER_ON', iden=self.__cameras[i].iden, timeout=60)

                if xbee_ack:  # Camera trap is alive and responsive

                    try:
                        with Timeout(60):  # 60 seconds to make a connection
                            # TODO: test built-in SFTP timeout and callbacks
                            # TODO: move login info to private file
                            # TODO: ensure camera hostname is set to camera ID, use human readible names (eg. bird species)
                            # TODO: set SFTP timeout connection

                            # Create FTP client ready to connect to camera
                            self.__sftp = SFTPClient('pi', 'raspberry', self.__cameras[i].iden + '.local')

                    except Timeout.Timeout:
                        logging.warn("TimeoutException: Connection to data station " + self.__cameras[i].iden + " failed")
                        # TODO: Continue mission

                    # FIXME: No matching 'if' for this 'else'
                    else:  # No exception: connection was made, let's try to download
                        try:
                            # Force TimeoutException if download is taking too long
                            with Timeout(self.__cameras[i].timeout):
                                self.__sftp.downloadAndDeleteAllFiles()
                                self.__cameras[i].download_complete = True

                        except Timeout.Timeout:
                            # Signal timed out
                            logging.warn("TimeoutException: Download timed out for data station " + self.__cameras[i].iden)

                        # Close down connection whether or not the download was successful
                        self.__sftp.close()

                    # Zane, insert download code here as thread.
                    # It should take in the 'camera_traps' queue and
                    # change the Camera.download_complete parameter if successful.
                    # Kill the thread if the Camera.timeout parameter is set to true.

                    # # Wait for timeout event, or download completion
                    # while True:
                    #     try:
                    #         cameras = camera_traps.get_nowait()
                    #         camera_traps.put(cameras)
                    #
                    #         if ((cameras[i].download_complete is True) or
                    #                 (cameras[i].timeout is True)):
                    #                 break
                    #
                    #         time.sleep(5)
                    #
                    #     except Empty:
                    #         pass

                    # Attempt to turn off camera trap
                    self.__xbee.send_command('POWER_OFF', iden=self.__cameras[i].iden, timeout=15)

                else:  # Camera not responsive
                    self.__cameras = self.__camera_traps.get_nowait()
                    self.__camera_traps.put(self.__cameras)
                    if self.__cameras[i].timeout is True:
                        break

                # No matter of status of download, we always stop FTP client
                self.__sftp.close()
