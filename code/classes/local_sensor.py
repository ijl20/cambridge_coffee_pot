"""
LocalSensor - direct readings in loop from sensor hub
"""

import asyncio
import time
import random

from classes.time_buffer import TimeBuffer, StatsBuffer

STATS_HISTORY_SIZE = 1000 # Define a stats_buffer with 1000 entries, each 1 second long
STATS_DURATION = 1

class LocalSensor():
    """
    LocalSensor polls a locally connected hardware sensor and sends values to the SensorHub.

    The local sensor is defined by instantiation argument "sensor" (e.g. a WeightSensor) which
    must provide the method "get_value()"
    """

    def __init__(self, settings=None, sensor_id=None, sensor=None, sensor_hub=None):
        print("LocalSensor() __init__ {}".format(sensor_id))

        self.settings = settings
        self.sensor_id = sensor_id
        self.sensor = sensor
        self.sensor_hub = sensor_hub

        # set counter for how many samples to collect before saving
        if self.settings is None or not "SAMPLE_SAVE_COUNT" in self.settings:
            self.save_count = 0
        else:
            self.save_count = self.settings["SAMPLE_SAVE_COUNT"]
        self.save_counter = 0 # cumulative count of how many samples we've collected
        print("Set save_count to", self.save_count)

        # Create a 30-entry x 1-second stats buffer
        self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE,
                                        duration=STATS_DURATION,
                                        settings=self.settings)

        #debug will have settings var for buffer size
        self.sample_buffer = TimeBuffer(size=1000, settings=self.settings, stats_buffer=self.stats_buffer)

        # Add the buffers to the sensor_hub object so it can use it in event tests
        self.sensor_hub.add_buffers( self.sensor_id,
                                     { "sample_buffer": self.sample_buffer,
                                       "stats_buffer": self.stats_buffer
                                     })

    # start() method is async with permanent loop, using asyncio.sleep().
    async def start(self):
        # minimum seconds between sensor readings
        SENSOR_READ_PERIOD = 0.1 # reading sensor at max 10Hz

        self.quit = False
        while not self.quit:
            ts = time.time()
            if self.sensor is None:
                value = random.random() * 100
            else:
                # no sensor provided, so generate random test values 0..100
                value = self.sensor.get_value()

            # save the reading to the sample_buffer
            self.sample_buffer.put(ts, value)

            # call the hub to process the reading, including test/send events to Platform
            await self.sensor_hub.process_reading(ts, self.sensor_id)

            # calculate time (seconds) taken to process reading
            process_time = time.time() - ts

            # If the process_time was more than 1 second, print log message
            if self.settings["LOG_LEVEL"] <= 2 and process_time > 1:
                print("{:.3f} LocalSensor {} process_time was {:.1f}".format(time.time(),
                                                                             self.sensor_id,
                                                                             process_time))

            # set the sleep time so total loop is at least SENSOR_READ_PERIOD
            sleep_time = SENSOR_READ_PERIOD - process_time
            if sleep_time < 0.01: # could be zero or negative, but we should always await
                sleep_time = 0.01

            # sleep 0.01 .. SENSOR_READ_PERIOD seconds.
            await asyncio.sleep(sleep_time)


    async def finish(self):
        self.quit = True
        print("local_sensor finish(): set to quit")

