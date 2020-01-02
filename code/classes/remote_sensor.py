"""
RemoteSensor - downstream sensors to Sensor Node
"""

import asyncio
import time
import simplejson as json
from simplejson.errors import JSONDecodeError

from classes.links import SensorMQTT as SensorLink
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

        #debug - StatsBuffer should have a FUNCTION to extract the value from the reading
        # Create a 30-entry x 1-second stats buffer
        #self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE,
        #                                duration=STATS_DURATION,
        #                                settings=self.settings)

        #debug setting var for buffer size
        self.sample_buffer = TimeBuffer(size=1000, settings=self.settings, stats_buffer=None )

        # Add the sample_buffer to the sensor_hub object so Events can use it in event tests
        self.sensor_hub.add_buffers(self.sensor_id, { "sample_buffer": self.sample_buffer } )

        self.sensor_link = SensorLink(settings=self.settings, topic=self.sensor_id+"/tele/SENSOR")

    async def start(self):
        await self.sensor_link.start()

        while True:
            message_obj = await self.sensor_link.get()
            packet = message_obj.publish_packet
            topic = packet.variable_header.topic_name

            print("remote_sensors() topic received {}".format(topic))

            message = ""
            if packet.payload is None:
                print("remote_sensors packet.payload=None {}".format(topic))
            elif packet.payload.data is None:
                print("remote_sensors() packet.payload.data=None {}".format(topic))
            else:
                message = packet.payload.data.decode('utf-8')
                print("remote_sensors() {} => {}".format(topic,message))

            message_dict = {}
            try:
                message_dict = json.loads(message)
            except JSONDecodeError:
                message_dict["message"] = message
                print("remote_sensors() json msg error: {} => {}".format(topic,message))

            message_dict["topic"] = topic

            ts = time.time()

            self.sample_buffer.put(ts, message_dict)

            await self.sensor_hub.process_reading(ts, self.sensor_id)

