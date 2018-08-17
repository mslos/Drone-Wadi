import logging
import os
import time
import threading

if not (os.getenv('DEVELOPMENT') == 'True'):
    import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

class StatusHandler(object):

    def __init__(self):

        self.__alive = True

        if not (os.getenv('DEVELOPMENT') == 'True'):
            GPIO.setwarnings(False) # Ignore warning for now
            GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
            GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
            GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)

        self.status = "PENDING"

    def run(self, led_status):

        while self.__alive and not (os.getenv('DEVELOPMENT') == 'True'):

            # Update status if needed
            if not led_status.empty():
                self.status = led_status.get()

            if self.status == "READY":
                GPIO.output(5, GPIO.HIGH) # Turn off green
                # Turn green LED on permanently
                GPIO.output(5, GPIO.HIGH) # Turn on
            elif self.status == "PENDING":
                GPIO.output(5, GPIO.LOW) # Turn off green
                # Flash red LED on and off
                GPIO.output(7, GPIO.HIGH) # Turn on
                sleep(1) # Sleep for 1 second
                GPIO.output(7, GPIO.LOW) # Turn off
                sleep(1) # Sleep for 1 second
            elif self.status == "FAILURE":
                GPIO.output(5, GPIO.LOW) # Turn off green
                # Turn red LED on permanently
                GPIO.output(7, GPIO.HIGH) # Turn on
            else:
                logging.error("Undefined state, no LED action")

    def stop(self):
        logging.info("Stoping status handler...")
        self.__alive = False
