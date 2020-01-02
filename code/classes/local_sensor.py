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

    def __init__(self, settings=None, sensor_id=None, events=None):
        print("LocalSensor() __init__ {}".format(sensor_id))

        self.settings = settings
        self.sensor_id = sensor_id
        self.events = events

        # Create a 30-entry x 1-second stats buffer
        self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE,
                                        duration=STATS_DURATION,
                                        settings=self.settings)

        #debug will have settings var for buffer size
        self.sample_buffer = TimeBuffer(size=1000, settings=self.settings, stats_buffer=None )

        # Add the buffers to the Events object so it can use it in event tests
        self.events.sensor_buffers[self.sensor_id] = { "sample_buffer": self.sample_buffer,
                                                       "stats_buffer": self.stats_buffer
                                                     }

    async def start(self):

        quit = False
        while not quit:
            rand = random.random() * 100
            ts = time.time()
            self.sample_buffer.put(ts, rand)
            await self.events.test(ts, self.sensor_id)
            await asyncio.sleep(0.1)
