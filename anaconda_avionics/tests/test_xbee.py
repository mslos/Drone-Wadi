import time
import logging

from anaconda_avionics.utilities.xbee import XBee

# TODO: Make this a proper HITL test on naked drone system
def test_xbee():
    xBee = XBee(serial_port="/dev/cu.usbserial-DN00OLOU")
    while True:
        xBee.send_command('street_cat', 'POWER_ON')
        if (xBee.acknowledge('street_cat', 'POWER_ON')):
            logging.debug("Success")
            break
        time.sleep(0.5)