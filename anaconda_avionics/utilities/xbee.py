import serial
import time
import logging
import os


class XBee(object):

    def __init__(self, serial_port="/dev/ttyUSB0"):

        self.xbee_port = None
        self.encode = None
        self.decode = None
        self.data_station_idens = None

        self.preamble_out = ['s', 't', 'r', 'e', 'e', 't']
        self.preamble_in = ['c', 'a', 't']

        while True:
            try:
                if not "DEVELOPMENT" in os.environ: # Don't connect to XBee while in development
                    self.xbee_port = serial.Serial(serial_port, 57600, timeout=5)
                    logging.info("Connected to XBee")
                else:
                    logging.info("In development mode, not connecting to XBee")
                break
            except serial.SerialException:
                logging.error("Failed to connect to xBee device. Retrying connection...")
                time.sleep(3)

        # TODO: make single dictionary
        self.encode = {
            'POWER_ON' : '1',
            'POWER_OFF' : '2',
            'EXTEND_TIME' : '3',
            'RESET_ID' : '4'
        }
        self.decode = {
            '1' : 'POWER_ON',
            '2' : 'POWER_OFF',
            '3' : 'EXTEND_TIME',
            '4' : 'RESET_ID',
        }

        self.data_station_idens = self.read_iden_map()

    def read_iden_map(self):
        return {
            'street_cat' : '01',
            'demon_cat' : '02'
        }

    def send_command(self, identity, command):

        # Immediately return False if in development (XBee not actually connected)
        if "DEVELOPMENT" in os.environ:
            return False

        logging.debug("xBee port write: %s" % self.preamble_out)
        self.xbee_port.write(self.preamble_out)

        logging.debug("xBee port write: %s" % self.data_station_idens[identity])
        self.xbee_port.write(self.data_station_idens[identity])

        logging.debug("xBee port write: %s" % self.encode[command])
        self.xbee_port.write(self.encode[command])

    def change_id(self, identity, new_id):
        self.send_command(identity, 'RESET_ID')
        self.xbee_port.write('<'+new_id+'>')

    def acknowledge(self, identity, command):
        """
        Called after command is sent
        """

        iden_match = False
        identity_index = 0

        preamble_success = False
        preamble_index = 0

        identity_code = self.data_station_idens[identity]
        command_code = self.encode[command]

        while (self.xbee_port.in_waiting > 0): # There's something in the XBee buffer
            incoming_byte = self.xbee_port.read() # Read a byte at a time
            logging.debug("XBee incoming byte: %s" % incoming_byte)

            # Third pass: Read command
            if (iden_match == True):
                return (incoming_byte == command_code)

            # Second pass: Check for identity match
            elif (preamble_success == True):
                if (incoming_byte == identity_code[identity_index]):
                    identity_index += 1
                else:
                    preamble_success = False
                    preamble_index = 0

                iden_match = (identity_index == 2)

            # First pass: Check for preamble match
            elif (incoming_byte == self.preamble_in[preamble_index]):
                preamble_index+=1
                preamble_success = (preamble_index == 3)

            # Reset
            else:
                iden_match = False
                preamble_success = False
                preamble_index = 0
                identity_index = 0

        return False # Unsuccessful ACK

if __name__ == "__main__":
    serial_port = raw_input("Enter serial port: ")
    xbee = XBee(serial_port)
    while True:
        try:
            command = raw_input("Enter Command \nPOWER_ON: 1\nPOWER_OFF: 2\nEXTEND_TIME: 3\nRESET_ID: 4\nCommand: ")
            try:
                if (command == '4'):
                    new_id = raw_input("New ID: ")
                    xbee.change_id('street_cat', new_id)
                else:
                    xbee.send_command('street_cat', xbee.decode[command])
            except KeyError:
                pass
        except KeyboardInterrupt:
            xbee.xbee_port.close()
