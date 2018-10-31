# Full stack data station wakeup-download-power down test

import queue
import time
import threading

from .timer import Timer
from .download import Download
from .xbee import XBee

# General infrastructure
rx_queue = queue.Queue()
wakeup_event = threading.Event()
download_event = threading.Event()
new_ds = threading.Event()
is_downloading = threading.Event()
is_awake = threading.Event()

dl = DataStationHandler(120000, 120000, 600000, rx_queue)

dl.run(wakeup_event, download_event, new_ds, is_downloading, is_awake)

target_station = raw_input("Enter target station ID: ")

rx_queue.put(target_station)
new_ds.set()

print("Waking up data station")
wakeup_event.set()

time.sleep(10)

print("Starting download")
download_event.set()
