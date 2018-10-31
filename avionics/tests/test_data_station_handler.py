import queue
import threading
import time
import unittest

from avionics.services.data_station_handler import DataStationHandler

class TestDataStationHandler(unittest.TestCase):

    def setUp(self):
        self._rx_queue = queue.Queue()
        self.wakeup_event = threading.Event()
        self.download_event = threading.Event()
        self.new_ds = threading.Event()
        self.is_downloading = threading.Event()
        self.is_awake = threading.Event()

        # One second connection timeout, read/write timeout, and 2 second overall timeout
        self._data_station_handler = DataStationHandler(1000, 1000, 2000, self._rx_queue)
        self._data_station_handler.connect()

    def tearDown(self):
        self._data_station_handler.stop()

    def test_full_stack(self):
        """Data station handler clears RX queue as it receives station IDs"""

        target_station = raw_input("Enter target station ID: ")

        self.rx_queue.put(target_station)
        self.new_ds.set()

        print("Waking up data station")
        self.wakeup_event.set()

        time.sleep(10)

        print("Starting download")
        self.download_event.set()

        self.assertEquals(self._rx_queue.qsize(), 0)
