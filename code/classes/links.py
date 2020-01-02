"""
MQTT links to Platform (Uplink) and remote sensors (SensorLink)
"""

import asyncio

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

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
