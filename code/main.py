# main.py

import sys
import asyncio

from classes.config import Config
from classes.sensor_node import SensorNode
from classes.utils import list_to_string

VERSION = "0.83"


if __name__ == '__main__':
    print("Cambridge Sensor Framework V{} started with {} arguments {}".format(VERSION, len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    settings = config.settings

    settings["VERSION"] = VERSION

    sensor_node = SensorNode(settings)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(sensor_node.start())
    except Exception as e:
        print("\nmain.py interrupted\n{}".format(e))

    loop.run_until_complete(sensor_node.finish())

    loop.close()

