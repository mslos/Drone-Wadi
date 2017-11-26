import serial
import time
from Queue import Queue, Empty
from utilities import Timer

class Xbee(object):

    def __init__(self, message_queue):
        self.xbee_port = connect_xbee(message_queue)
        self.encode = {
        'Power On' : 0,
        'Power Off' : 1,
        'Power Status' : 2,
        'Indentify:' : 3
        }
        self.decode = {
        0 : 'Power On',
        1 : 'Power Off',
        2 : 'Power Status'
        3 : 'Identify'
        }

    def connect_xbee(message_queue):
        while True:
            try:
                xbee_port = serial.Serial("/dev/ttyUSB0", 9600, timeout = 5)
                break
            except serial.SerialException:
                message_queue.put("Failed to connect to xBee Device")
                time.sleep(5)

    def send_command(command, iden=0, timeout=0):
        timer = Timer()
        while True:
            response = [-1, -1]
            # Send command, addressed to correct iden, through serial port
            xbee_port.write(iden)
            xbee_port.write(self.encode(command))

            # try to read the serial port (2bytes), timeout for read = 5s
            respose_raw = xbee_port.read(2)
            if response_raw:
                response[0] = response_raw[0]
                response[0] = self.decode(response_raw[0])

                # check to see if we got the desired response
                if (response[0] == iden or iden == 0) and response[1] == command:
                    return response

            # check for timeout
            if (timer.time_elapsed() > timeout and timeout != 0):
                return False
