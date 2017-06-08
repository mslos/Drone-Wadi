from Queue import Queue
from plane_navigation_script0 import Timer

def log(message_queue, message):
    message_queue.put(message)

def mission_logger(message_queue):
    mission_time = Timer()

    log_filename = "mission_raspi_log.txt"
    log_file = open(log_filename, "a")
    log_file.write("############### NEW MISSION ###############")

    while True:
        message = message_queue.get()
        if (message != None):
            log_file.write(mission_time.timeStamp() + message)
            print (mission_time.timeStamp() + message)
