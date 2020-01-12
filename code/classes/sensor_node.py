# sensor_node.py

import asyncio
import time

from classes.sensor_hub import SensorHub
from classes.remote_sensor import RemoteSensor
from classes.local_sensor import LocalSensor
from classes.weight_sensor import WeightSensor
from classes.watchdog import Watchdog

GPIO_FAIL = False
try:
    import RPi.GPIO as GPIO
except (ImportError,RuntimeError):
    GPIO_FAIL = True
    print("RPi.GPIO not loaded, running in SIMULATION_MODE")

class SensorNode(object):
    """
    SensorNode(settings) is the "main" class for the sensor node, providing async methods:

    async start() - instantiates SensorHub, LocalSensors, RemoteSensors, Watchdog
              and runs them in parallel as co-routines.

    async finish() - attempts cleanup when SensorNode has been signalled to end.
    """

    def __init__(self, settings=None):
        global GPIO_FAIL

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

