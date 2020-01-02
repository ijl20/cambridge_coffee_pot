import sys
import logging
import asyncio
import time
import random

import simplejson as json
from simplejson.errors import JSONDecodeError

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from classes.sensor_utils import list_to_string
from classes.time_buffer import TimeBuffer, StatsBuffer
from classes.config import Config

STATS_HISTORY_SIZE = 1000 # Define a stats_buffer with 1000 entries, each 1 second long
STATS_DURATION = 1

VERSION = "0.81a"

class Uplink(object):

    def __init__(self, settings=None):
        print("Uplink __init__()")
        self.settings = settings
        self.client = MQTTClient()

    async def start(self):
        print('start() startup')
        await self.client.connect(self.settings["UPLINK_HOST"])
        print('start() connected {}'.format(self.settings["UPLINK_HOST"]))

    async def send(self, topic, message=None):
        print('uplink send() sending {}'.format(topic))
        message_b = bytes(message,'utf-8')
        tasks = [
            asyncio.ensure_future(self.client.publish(topic, message_b))
        ]
        await asyncio.wait(tasks)
        print("uplink send() published {} {}".format(topic,message))

    async def finish(self):
        await self.client.disconnect()

class SensorLink(object):
    """
    SensorLink provides the local communications endpoint for receiving
    data from the remote sensors within the SensorNode
    """

    def __init__(self, settings=None, topic=None):
        print("SensorLink __init__() {}".format(topic))
        self.settings = settings
        self.topic = topic

    async def start(self):
        print("SensorLink start() {}".format(self.topic))
        self.client = MQTTClient(config=None)

        await self.client.connect(self.settings["SENSOR_HOST"])
        print("SensorLink {} connected".format(self.topic))

        await self.client.subscribe([(self.topic, QOS_0)])
        print("SensorLink {} subscribed".format(self.topic))

    async def get(self):
        return await self.client.deliver_message()

    async def stop(self):
        await self.client.disconnect()
        print("remote_sensor {} disconnected".format(self.topic))

class Events(object):
    """
    The Events object provides a .test() function that looks at the values in the various sensor buffers and
    decides whether an event should be sent to the platform.
    """

    def __init__(self, settings=None):
        print("Events __init()__")
        self.settings = settings

        # Create event buffer for sensor node, i.e. common to all sensors
        self.event_buffer = TimeBuffer(size=1000, settings=settings)

        # Create dictionary to reference buffers for each sensor
        # This Events object will be passed to each sensor __init__ so the sensor will add its buffers to sensor_buffers.
        self.sensor_buffers = {}

        self.event_buffer = TimeBuffer(100)

        # Connect to the platform
        self.uplink = Uplink(settings=self.settings)

    async def start(self):
        await self.uplink.start()

        # Send startup message
        startup_event = { "acp_ts": time.time(),
                        "acp_id": self.settings["SENSOR_ID"],
                        "event_code": "COFFEE_STARTUP"
                        }

        startup_msg = json.dumps(startup_event)

        #send MQTT topic, message
        await self.uplink.send(self.settings["SENSOR_ID"], startup_msg)

    def test_event_remote(self, ts, sensor_id):
        # test if remote sensor (penultimate char = '-')
        if sensor_id[-2:-1] == "-":

            print("test_event_remote() {}".format(sensor_id))

            sample = self.sensor_buffers[sensor_id]["sample_buffer"].get(0)

            #debug send event for every message from remote sensors
            if True:
                remote_event = { "acp_ts": ts,
                                 "acp_id": sensor_id,
                                 "event_code": "COFFEE_REMOTE",
                                 "event_value": sample["value"]
                               }
                return remote_event

        return None

    def test_event_local(self, ts, sensor_id):
        if not sensor_id[-2:-1] == "-":
            sample = self.sensor_buffers[sensor_id]["sample_buffer"].get(0)

            if not sample is None and sample["value"] > 99:
                print("test_event_local() {}".format(sensor_id))
                local_event = { "acp_ts": ts,
                                "acp_id": sensor_id,
                                "event_code": "COFFEE_LOCAL",
                                "event_value": sample["value"]
                              }
                return local_event

        return None

    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    def test(self, ts, sensor_id):
        events = []
        for test_function in [ self.test_event_remote,
                               self.test_event_local
                    ]:
            event = test_function(ts, sensor_id)
            if not event is None:
                events.append(event)

        return events

class RemoteSensor():
    """
    RemoteSensor represents a sensor within the Node connected remotely, e.g. via
    a local wifi ssid broadcast by the sensor hub.
    """

    def __init__(self, settings=None, sensor_id=None, events=None):
        print("RemoteSensor() __init__ {}".format(sensor_id))

        self.settings = settings
        self.sensor_id = sensor_id
        self.events = events

        #debug - StatsBuffer should have a FUNCTION to extract the value from the reading
        # Create a 30-entry x 1-second stats buffer
        #self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE,
        #                                duration=STATS_DURATION,
        #                                settings=self.settings)

        #debug setting var for buffer size
        self.sample_buffer = TimeBuffer(size=1000, settings=self.settings, stats_buffer=None )

        # Add the sample_buffer to the Events object so it can use it in event tests
        self.events.sensor_buffers["sensor_id"] = { "sample_buffer": self.sample_buffer }

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

            await self.events.test(ts, sensor_id)


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

async def main():
    print("main V{} started with {} arguments {}".format(VERSION, len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    settings = config.settings

    settings["VERSION"] = VERSION

    events = Events(settings=settings)

    await events.start()

    remote_sensor_a = RemoteSensor( settings=settings,
                                    sensor_id="sensor-node-test-a", 
                                    events=events)

    remote_sensor_b = RemoteSensor( settings=settings,
                                    sensor_id="sensor-node-test-b", 
                                    events=events)

    local_sensor = LocalSensor( settings=settings,
                                sensor_id="sensor-node-test-weight", 
                                events=events)

    await asyncio.gather(local_sensor.start(),
                         remote_sensor_a.start(),
                         remote_sensor_b.start()
                        )


if __name__ == '__main__':
    print('hbmqtt startup')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
