#!/usr/bin/python

import serial, sys
import os, fnmatch, time

'''
Use of this script:

python configure_xbee.py CAMERA_ID ENCRPYTION_CONTROL_BIT

e.g.
python configure_xbee.py 1 0 # xbee id is 1 and encryption is off
python configure_xbee.py 5 1 # xbee id is 5 and encryption is on

'''

# Values to be changed for better security
ATID_value = "3001"
ATDH_value = "0"
ATDL_value = "2"
time_wait = 0.1

# AES encryption is in experimental stage
ATKY_value = "11111222223333344444555556666677" # CAREFUL: Do not publish encryption key publically! This is just an example.
'''# key is a 32 hexadecimal character string. Example: 11111222223333344444555556666677
https://www.digi.com/resources/documentation/Digidocs/90001110-88/tasks/t_set_up_basic_encryption_for_your_xbee_network.htm
'''

def find_file(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def write_to_xbee(value, ser):
    ser.flushInput()
    ser.flushOutput()
    ser.write(value)
    line = ser.read(2)
    if line[0] == 'O':
        print value.replace('\r\n','')+" written successfully."
    ser.flushInput()
    ser.flushOutput()

def config_xbee_my(my_id, ser):
    write_to_xbee("+++", ser)
    time.sleep(time_wait)
    write_to_xbee("ATID "+ATID_value+'\r\n', ser)
    time.sleep(time_wait)
    write_to_xbee("ATDH "+ ATDH_value+'\r\n', ser)
    time.sleep(time_wait)
    write_to_xbee("ATDL "+ ATDL_value+'\r\n', ser)
    time.sleep(time_wait)
    write_to_xbee("ATMY "+ str(my_id)+'\r\n', ser)
    time.sleep(time_wait)
    write_to_xbee("ATWR"+'\r\n', ser)

# key is a 32 hexadecimal character string. Example: 11111222223333344444555556666677
def config_encryption(ser, activated="0", key="0"):
    if (activated == "1"):
        time.sleep(time_wait)
        write_to_xbee("ATEE 1"+'\r\n', ser)
        time.sleep(time_wait)
        write_to_xbee("ATKY "+str(key)+'\r\n', ser)
        print "Encryption activated."
    else:
        write_to_xbee("ATEE 0"+'\r\n', ser)
        print "Encryption NOT activated."
    time.sleep(time_wait)
    write_to_xbee("ATWR"+'\r\n', ser)


def main():
    print sys.argv
    try:
        ATMY_value = str(sys.argv[1])
    except:
        print "Camera ID not provided"
        return
    try:
        encryption_bool = str(sys.argv[2])
    except:
        print "Encryption bit not provided, setting encryption_bool to 0."
        encryption_bool = 0
    port_name = find_file('tty.usbserial*', '/dev/')
    with serial.Serial(port_name[0], 9600) as serial_port:
        serial_port.bytesize = serial.EIGHTBITS
        serial_port.parity = serial.PARITY_NONE
        serial_port.stopbits = serial.STOPBITS_ONE
        config_xbee_my(ATMY_value,serial_port)
        config_encryption(serial_port, encryption_bool, ATKY_value)

if __name__ == "__main__":
    main()
