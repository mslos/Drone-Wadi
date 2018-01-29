import serial
import time
import logging
import os

from anaconda_avionics.utilities import Timer

class XBeeResponse(object):

    message = None
    command = None

    def __init__(self):
        pass


class XBee(object):

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
                logging.error("Failed to connect to xBee device. Retrying connection...")
                time.sleep(3)

        # TODO: make single dictionary
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

    # TODO: Make XBee not expect an integer identity, but still maintain small command size
    def sendCommand(self, command, identity=0, timeout=0):

        # Immediately return False if in development and XBee not actually connected
        if "DEVELOPMENT" in os.environ:
            return False

        xbee_timer = Timer()
        while True:
            response = XBeeResponse()

            # Send command, addressed to correct identity, through serial port
            self.xbee_port.write(identity)
            self.xbee_port.write(self.encode[command])

            # Try to read the serial port (2 bytes), timeout for read = 5s
            response_raw = self.xbee_port.read(2)

            # If some response has come back from the data station
            if response_raw:
                response.message = self.decode[response_raw[0]]

                # Check to see if we got the desired response
                if (response.message == identity or identity == 0) and response.command == command:
                    return response

            # Check for timeout
            if (xbee_timer.time_elapsed() > timeout and timeout != 0):
                return False
