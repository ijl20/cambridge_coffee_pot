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

VERSION = "0.81d"

class SensorNode(object):

    def __init__(self, settings=None):
        global GPIO_FAIL

        self.ALLOW_UPLINK = False

        self.settings = settings

        if self.settings is None:
            self.settings = { }

        if not "VERSION" in self.settings:
            self.settings["VERSION"] = VERSION

        # ensure settings["DISPLAY_SIMULATION_MODE"] is set
        if not "DISPLAY_SIMULATION_MODE" in self.settings:
            self.settings["DISPLAY_SIMULATION_MODE"] = GPIO_FAIL

        if self.settings["DISPLAY_SIMULATION_MODE"]:
            print("Using DISPLAY_SIMULATION_MODE")

        if not self.ALLOW_UPLINK:
            print("Uplink to Platform disabled")


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

    def finish(self):
        print("\n")

        if not self.DISPLAY_SIMULATION_MODE:

            self.display.finish()

            print("GPIO cleanup()...")

        if not GPIO_FAIL:
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
    loop.run_until_complete(sensor_node.start())
    loop.close()
