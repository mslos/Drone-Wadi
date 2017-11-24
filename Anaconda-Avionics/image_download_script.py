import serial
import threading
import time
from Queue import Queue, Empty
from xbee_comm import Xbee

def downoad_sequence(camera_traps, message_queue):

    cameras = camera_traps.get_nowait()
    camera_traps.put(cameras)

    # Create and connect to xBee module
    xbee = Xbee(message_queue)

    # For wach desired camera trap, turn on, download, turn off
    for i in range(length(cameras)):

        # Broadcast a directed "Power On" Command to the desired camera trap
        while True:
            xbee_ack = xbee.send_command('Power On', iden=cameras[i].iden, 60)
            if xbee_ack:

                # Start downloading
                # Zane, insert download code here as thread.
                # It should take in the 'camera_traps' queue and
                # change the Camera.download_complete parameter if successful.
                # Kill the thread if the Camera.timout parameter is set to true.

                # Wait for timeout event, or download completion
                while True:
                    try:
                        cameras = camera_traps.get_nowait()
                        camera_traps.put(cameras)

                        if ((cameras[i].download_complete is True) or
                                (cameras[i].timeout is True)):
                                break

                        time.sleep(5)

                    except Empty:
                        pass

                # Attempt to turn off camera trap
                xbee.send_command('Power Off', iden=cameras[i].iden, timeout=15)

            else:
                cameras = camera_traps.get_nowait()
                camera_traps.put(cameras)
                if cameras[i].timeout is True:
                    break
