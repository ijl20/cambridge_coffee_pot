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

GPIO_FAIL = False
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO_FAIL = True
    print("RPi.GPIO not loaded, running in SIMULATION_MODE")

VERSION = "0.82"

class SensorNode(object):

    def __init__(self, settings=None):
        global GPIO_FAIL

        #debug this can come from settings
        self.ALLOW_UPLINK = False

        self.settings = settings

        if self.settings is None:
            self.settings = { }

        if not "VERSION" in self.settings:
            self.settings["VERSION"] = VERSION

        if "DISPLAY_SIMULATION_MODE" in self.settings and self.settings["DISPLAY_SIMULATION_MODE"]:
            print("Using DISPLAY_SIMULATION_MODE=True from settings file")

        # ensure settings["DISPLAY_SIMULATION_MODE"] is set
        if not "DISPLAY_SIMULATION_MODE" in self.settings:
            self.settings["DISPLAY_SIMULATION_MODE"] = GPIO_FAIL

        if not self.ALLOW_UPLINK:
            print("Uplink to Platform disabled")


    async def start(self):

        self.sensor_hub = SensorHub(settings=self.settings)

        await self.sensor_hub.start(time.time())

        self.remote_sensor_a = RemoteSensor( settings=self.settings,
                                        sensor_id="csn-node-test-a",
                                        sensor_hub=self.sensor_hub)

        self.remote_sensor_b = RemoteSensor( settings=self.settings,
                                        sensor_id="csn-node-test-b",
                                        sensor_hub=self.sensor_hub)

        self.local_sensor = LocalSensor( settings=self.settings,
                                    sensor_id="csn-node-test-weight",
                                    sensor=WeightSensor(settings=self.settings),
                                    sensor_hub=self.sensor_hub)

        self.watchdog = Watchdog( settings=self.settings, watched=self.sensor_hub, period=30)

        await asyncio.gather(self.local_sensor.start(),
                             self.remote_sensor_a.start(),
                             self.remote_sensor_b.start(),
                             self.watchdog.start()
                            )

    async def finish(self):
        print("\n")

        await self.watchdog.finish()

        await self.remote_sensor_a.finish()

        await self.remote_sensor_b.finish()

        await self.local_sensor.finish()

        await self.sensor_hub.finish()

        if not GPIO_FAIL:
            print("GPIO cleanup()...")
            GPIO.cleanup()

        print("SensorNode finished")


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

