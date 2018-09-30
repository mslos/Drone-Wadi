import logging
import os
import time
import threading

if not (os.getenv('DEVELOPMENT') == 'True'):
    import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

class StatusHandler(object):

    def __init__(self):

        self.__alive = True
        self.RED_PIN = 5
        self.GREEN_PIN = 7

        if not (os.getenv('DEVELOPMENT') == 'True'):
            GPIO.setwarnings(False) # Ignore warning for now
            GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
            GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
            GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)

        self.status = "INITIALIZING"

    def run(self, led_status):

        while self.__alive and not (os.getenv('DEVELOPMENT') == 'True'):
            # Update status if needed
            if not led_status.empty():
                self.status = led_status.get()
                led_status.task_done()
                logging.info("LED Status: %s", self.status)

            # Display status via LED UI
            if self.status == "INITIALIZING":
                # Turn both LEDs on to verify that they are both working
                GPIO.output(self.RED_PIN, GPIO.HIGH)
                GPIO.output(self.GREEN_PIN, GPIO.HIGH)
                time.sleep(3) # Block to give the operator enough time to verify

            elif self.status == "READY":
                GPIO.output(self.RED_PIN, GPIO.LOW) # Turn off red
                # Turn green LED on permanently
                GPIO.output(self.GREEN_PIN, GPIO.HIGH) # Turn on

            elif self.status == "PENDING":
                GPIO.output(self.GREEN_PIN, GPIO.LOW) # Turn off green
                # Flash red LED on and off
                GPIO.output(self.RED_PIN, GPIO.HIGH) # Turn on
                time.sleep(0.5) # Sleep for 0.5 second
                GPIO.output(self.RED_PIN, GPIO.LOW) # Turn off
                time.sleep(0.5) # Sleep for 0.5 second

            elif self.status == "FAILURE":
                GPIO.output(self.GREEN_PIN, GPIO.LOW) # Turn off green
                # Turn red LED on permanently
                GPIO.output(self.RED_PIN, GPIO.HIGH) # Turn on

            else:
                logging.error("Undefined state, no LED action")
                # Turn off both LEDs
                GPIO.output(self.RED_PIN, GPIO.LOW)
                GPIO.output(self.GREEN_PIN, GPIO.LOW)

    def stop(self):
        logging.info("Stoping status handler...")

        # Turn off the LEDs
        if not (os.getenv('DEVELOPMENT') == 'True'):
            GPIO.output(self.RED_PIN, GPIO.LOW)
            GPIO.output(self.GREEN_PIN, GPIO.LOW)

        # Kill the run method
        self.__alive = False
