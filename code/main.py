# main.py

"""
This is the startup program that launches the async SensorNode.
"""

import sys
import asyncio
import signal

from classes.config import Config
from classes.sensor_node import SensorNode
from classes.utils import list_to_string

VERSION = "0.83"

# The asyncio Event the tasks will listen for to cleanup
FINISH_EVENT = asyncio.Event()

# The loop signal handler callback
def finish(*args):
    print("main() finish() called")
    global FINISH_EVENT
    FINISH_EVENT.set()

if __name__ == '__main__':
    print("Cambridge Sensor Framework V{} started with {} arguments {}".format(VERSION, len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    settings = config.settings

    settings["VERSION"] = VERSION

    sensor_node = SensorNode(settings=settings, finish_event=FINISH_EVENT)

    loop = asyncio.get_event_loop()

    loop.add_signal_handler(signal.SIGINT, finish)
    loop.add_signal_handler(signal.SIGTERM, finish)

    loop.run_until_complete(sensor_node.start())
