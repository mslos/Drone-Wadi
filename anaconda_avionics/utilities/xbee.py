import serial
import time
import logging
import os

from anaconda_avionics.utilities import Timer

class Xbee(object):

    xbee_port = None
    encode = None
    decode = None

    def __init__(self):

        while True:
            try:
                if not "DEVELOPMENT" in os.environ: # Don't connect to XBee while in development
                    self.xbee_port = serial.Serial("/dev/ttyUSB0", 9600, timeout=5)
                    logging.info("Connected to XBee")
                else:
                    logging.info("In development mode, not connecting to XBee")
                break
            except serial.SerialException:
                logging.warn("Failed to connect to xBee device. Retrying connection...")
                time.sleep(3)

        self.encode = {
            'POWER_ON' : 0,
            'POWER_OFF' : 1,
            'POWER_STATUS' : 2,
            'IDENTIFY' : 3
        }
        self.decode = {
            0 : 'POWER_ON',
            1 : 'POWER_OFF',
            2 : 'POWER_STATUS',
            3 : 'IDENTIFY'
        }

    def send_command(self, command, iden=0, timeout=0):
        timer = Timer()

        while True:
            response = [-1, -1]
            # Send command, addressed to correct iden, through serial port
            self.xbee_port.write(iden)
            self.xbee_port.write(self.encode[command])

            # try to read the serial port (2bytes), timeout for read = 5s
            response_raw = self.xbee_port.read(2)
            if response_raw:
                response[0] = response_raw[0]
                response[0] = self.decode[response_raw[0]]

                # check to see if we got the desired response
                if (response[0] == iden or iden == 0) and response[1] == command:
                    return response

            # check for timeout
            if (timer.time_elapsed() > timeout and timeout != 0):
                return False
