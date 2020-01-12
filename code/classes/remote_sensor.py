"""
RemoteSensor - downstream sensors to Sensor Node
"""

import asyncio
import time

#from classes.links_hbmqtt import LinkHBMQTT as SensorLink
from classes.links_gmqtt import LinkGMQTT as SensorLink
from classes.time_buffer import TimeBuffer, StatsBuffer

STATS_HISTORY_SIZE = 1000 # Define a stats_buffer with 1000 entries, each 1 second long
STATS_DURATION = 1

class RemoteSensor():
    """
    RemoteSensor represents a sensor within the Node connected remotely, e.g. via
    a local wifi ssid broadcast by the sensor hub.
    """

    def __init__(self, settings=None, sensor_id=None, sensor_hub=None):
        print("RemoteSensor() __init__ {}".format(sensor_id))

        self.settings = settings
        self.sensor_id = sensor_id
        self.sensor_hub = sensor_hub

        self.quit = False
        self.finish_event = asyncio.Event()

        #debug - StatsBuffer should have a FUNCTION to extract the value from the reading
        # Create a 30-entry x 1-second stats buffer
        #self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE,
        #                                duration=STATS_DURATION,
        #                                settings=self.settings)

        #debug setting var for buffer size
        self.sample_buffer = TimeBuffer(size=1000, settings=self.settings, stats_buffer=None )

        # Add the sample_buffer to the sensor_hub object so Events can use it in event tests
        self.sensor_hub.add_buffers(self.sensor_id, { "sample_buffer": self.sample_buffer } )

        self.sensor_link = SensorLink(settings=self.settings)


    async def start(self):
        link_settings = {}
        link_settings["host"] = self.settings["SENSOR_HOST"]
        await self.sensor_link.start(link_settings)
        
        subscribe_settings = {}
        subscribe_settings["topic"] = self.sensor_id+"/tele/SENSOR"
        await self.sensor_link.subscribe(subscribe_settings)

        while True:
            get_task = asyncio.ensure_future(self.sensor_link.get())
            finish_task = asyncio.ensure_future(self.finish_event.wait())

            finished, pending = await asyncio.wait( [ get_task, finish_task ],
                                                    return_when=asyncio.FIRST_COMPLETED )

            # was self.quit just set in self.finish()?
            if self.quit:
                break

            message = finished.pop().result()
            
            ts = time.time()

            self.sample_buffer.put(ts, message)

            await self.sensor_hub.process_reading(ts, self.sensor_id)

        print("RemoteSensor() {} finished".format(self.sensor_id))

    async def finish(self):
        print("RemoteSensor {} set to finish".format(self.sensor_id))
        self.quit = True
        self.finish_event.set()

        await self.sensor_link.finish()

        print("RemoteSendor() {} finish completed".format(self.sensor_id))
