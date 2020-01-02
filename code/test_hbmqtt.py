import sys
import logging
import asyncio
import time

from classes.sensor_utils import list_to_string
from classes.config import Config
from classes.remote_sensor import RemoteSensor
from classes.local_sensor import LocalSensor
from classes.sensor_hub import SensorHub
from classes.weight_sensor import WeightSensor
from classes.watchdog import Watchdog

VERSION = "0.81d"

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
        sensor_hub = SensorHub(settings=self.settings)

        await sensor_hub.start(time.time())

        remote_sensor_a = RemoteSensor( settings=self.settings,
                                        sensor_id="csn-node-test-a", 
                                        sensor_hub=sensor_hub)

        remote_sensor_b = RemoteSensor( settings=self.settings,
                                        sensor_id="csn-node-test-b", 
                                        sensor_hub=sensor_hub)

        local_sensor = LocalSensor( settings=self.settings,
                                    sensor_id="csn-node-test-weight", 
                                    sensor=WeightSensor(settings=self.settings),
                                    sensor_hub=sensor_hub)

        watchdog = Watchdog( settings=self.settings, watched=sensor_hub, period=30)

        await asyncio.gather(local_sensor.start(),
                             remote_sensor_a.start(),
                             remote_sensor_b.start(),
                             watchdog.start()
                            )


if __name__ == '__main__':
    print('Sensor Node startup')
    sensor_node = SensorNode()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sensor_node.start())
    loop.close()
