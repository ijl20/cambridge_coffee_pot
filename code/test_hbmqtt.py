import sys
import logging
import asyncio
import time

import simplejson as json
from simplejson.errors import JSONDecodeError

from classes.sensor_utils import list_to_string
from classes.time_buffer import TimeBuffer, StatsBuffer
from classes.config import Config
from classes.remote_sensor import RemoteSensor
from classes.local_sensor import LocalSensor
from classes.sensor_hub import SensorHub

VERSION = "0.81c"

class SensorNode(object):
    def __init__(self):
        print("SensorNode V{} started with {} arguments {}".format(VERSION, len(sys.argv), list_to_string(sys.argv)))

        if len(sys.argv) > 1 :
            filename = sys.argv[1]
            config = Config(filename)
        else:
            config = Config()

        self.settings = config.settings

        self.settings["VERSION"] = VERSION

    async def start(self):
        sensor_hub = SensorHub(settings=settings)

        await sensor_hub.start(time.time())

        remote_sensor_a = RemoteSensor( settings=settings,
                                        sensor_id="csn-node-test-a", 
                                        events=events)

        remote_sensor_b = RemoteSensor( settings=settings,
                                        sensor_id="csn-node-test-b", 
                                        events=events)

        local_sensor = LocalSensor( settings=settings,
                                    sensor_id="csn-node-test-weight", 
                                    events=events)

        await asyncio.gather(local_sensor.start(),
                             remote_sensor_a.start(),
                             remote_sensor_b.start()
                            )


if __name__ == '__main__':
    print('Sensor Node startup')
    sensor_node = SensorNode()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sensor_node.start())
    loop.close()
