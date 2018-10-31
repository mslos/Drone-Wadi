import queue
import threading
import time
import unittest

from services.data_station_handler import DataStationHandler

class TestDataStationHandler(unittest.TestCase):

    def setUp(self):
        self.rx_queue = queue.Queue()
        self.wakeup_event = threading.Event()
        self.download_event = threading.Event()
        self.is_downloading = threading.Event()
        self.is_awake = threading.Event()

        # One second connection timeout, read/write timeout, and 2 second overall timeout
        self._data_station_handler = DataStationHandler(1000, 1000, 2000, self.rx_queue)
        self._data_station_handler.connect()

    def tearDown(self):
        self._data_station_handler.stop()

    def test_full_stack(self):
        """Data station handler clears RX queue as it receives station IDs"""

        self.rx_queue.put("321")

        print("Waking up data station")
        self.wakeup_event.set()
        self.download_event.set()
        
        self._data_station_handler._wake_download_and_sleep(self.wakeup_event, self.download_event, self.is_downloading, self.is_awake)



        print(self.rx_queue.get())

        self.assertEquals(self.rx_queue.qsize(), 0)
