"""
General utilities (functions and objects) used for data mule mission code.
"""

import time
from Queue import Empty

## TIMER OBJECT
class Timer(object):
    """
    Timer function that monitors time elapsed when started.
    """
    def __init__(self):
        self.start_timer()

    def start_timer(self):
        """Start the timer"""
        self.start = time.time()

    def time_elapsed(self):
        """Return the time elapsed since the timer was started"""
        return time.time()-self.start

    def time_stamp(self):
        """Create and return a time stamp string for logging purposes"""
        seconds = self.time_elapsed()
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return "%d:%02d:%02d: " % (hours, mins, secs)

class Logger(object):
    """
    Class manages all messages and compiles them into a sigle log file.
    """

    def __init__(self, date, start_time, message_queue):
        self.filename = "mission_log_%s_%s.txt" % (date, start_time)
        self.file = open(self.filename, 'w')
        self.file.write('Mission Log for %s, %s' % (date, time))
        self.file.close()
        self.message_queue = message_queue
        self.timer = Timer()

    def start_logging(self):
        """
        This function is meant to run continuously by checking a queue for new
        log messages.
        """

        while True:
            try:
                message = self.message_queue.get_nowait()
                log_entry = '[%s]: %s' % (self.timer.time_stamp, message)
                self.file = open(self.filename, 'a')
                self.file.write(log_entry)
                self.file.close()
                print log_entry
                if message == 'mission_end':
                    break

            except Empty:
                pass

    def single_entry(self, message):
        """
        Single log book entries.
        """

        log_entry = '[%s]: %s' % (self.timer.time_stamp, message)
        self.file = open(self.filename, 'a')
        self.file.write(log_entry)
        self.file.close()
        print log_entry
