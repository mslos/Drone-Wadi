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
                log_entry = '[%s]: %s' % (self.timer.time_stamp(), message)
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

        log_entry = '[%s]: %s' % (self.timer.time_stamp(), message)
        self.file = open(self.filename, 'a')
        self.file.write(log_entry)
        self.file.close()
        print log_entry