import serial
import threading
import time
from Queue import Queue, Empty
from xbee_comm import Xbee
from ftp_client import DroneClient
from utilities import Timeout

def download_sequence(camera_traps, message_queue):

    cameras = camera_traps.get_nowait()
    camera_traps.put(cameras)

    # Create and connect to xBee module
    xbee = Xbee(message_queue)

    # For wach desired camera trap, turn on, download, turn off
    for i in range(length(cameras)):

        # Broadcast a directed "Power On" Command to the desired camera trap
        while True:
            xbee_ack = xbee.send_command('Power On', iden=cameras[i].iden, 60)

            if xbee_ack: # Camera trap is alive and responsive

                try:
                    with Timeout(60): # 60 seconds to make a connection
                        # Create FTP client ready to connect to camera
                        # This class busy waits until a connection is made
                        ftp_client = DroneClient('../login_credentials.config', 'localhost')

                except Timeout.Timeout:
                    print "TimeoutException: Connection to camera trap failed."

                else: # No exception: connection was made, let's try to download
                    try:
                        # Force TimeoutException if download is taking too long
                        with Timeout(cameras[i].timeout):
                            ftp_client.downloadAllPhotos()
                            Camera.download_complete == True # FIXME: why do we need this?

                    except Timeout.Timeout:
                        # Signal timed out
                        print "TimeoutException: Download timed out for camera " + i

                    # Close down connection whether or not the download was successful
                    ftp_client.quit()

                # Zane, insert download code here as thread.
                # It should take in the 'camera_traps' queue and
                # change the Camera.download_complete parameter if successful.
                # Kill the thread if the Camera.timout parameter is set to true.

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
                xbee.send_command('Power Off', iden=cameras[i].iden, timeout=15)

            else:
                cameras = camera_traps.get_nowait()
                camera_traps.put(cameras)
                if cameras[i].timeout is True:
                    break

    # No matter of status of download, we always stop FTP client
    ftp_client.quit()
