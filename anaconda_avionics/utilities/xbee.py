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

        self.preamble_out = ['s', 't', 'e', 'e', 't']
        self.preamble_in = ['c', 'a', 't']

        while True:
            try:
                if not "DEVELOPMENT" in os.environ: # Don't connect to XBee while in development
                    self.xbee_port = serial.Serial(serial_port, 9600, timeout=5)
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
            'EXTEND_TIME' : '3'
        }
        self.decode = {
            '1' : 'POWER_ON',
            '2' : 'POWER_OFF',
            '3' : 'EXTEND_TIME'
        }

        self.data_station_idens = self.read_iden_map()

    def read_iden_map(self):
        return {
            'street_cat' : '01',
            'demon_cat' : '02'
        }

    def send_command(self, identity, command):

        # Immediately return False if in development and XBee not actually connected
        if "DEVELOPMENT" in os.environ:
            return False

        self.xbee_port.write(self.preamble_out)

        self.xbee_port.write(self.data_station_idens[identity])

        self.xbee_port.write(self.encode[command])

    def acknowledge(self, identity, command):

        iden_match = False
        preamble_success = False
        preamble_count = 0
        iden_count = 0

        identity_code = self.data_station_idens[identity]
        command_code = self.encode[command]

        while (self.xbee_port.in_waiting > 0):
            incomming_byte = self.xbee_port.read()
            print incomming_byte
            return True

            if (iden_match == True):
                return (incomming_byte == command_code)

            elif (preamble_success == True):
                if (incomming_byte == identity_code[iden_count]):
                    iden_count += 1
                else:
                    preamble_success = False
                    preamble_count = 0

                iden_match = (iden_count == 2);

            elif (incomming_byte == self.preamble_in[preamble_count]):
                preamble_count+=1;
                preamble_success = (preamble_count == 3);

            else:
                gate = 0;

        return False

if __name__ == '__main__':
    xBee = XBee()
    while True:
        xBee.send_command('street_cat', 'POWER_ON')
        if (xBee.acknowledge('street_cat', 'POWER_ON')):
            print 'yay'
        time.sleep(0.5)
