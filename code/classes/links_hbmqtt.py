"""
MQTT links to Platform (PlatformMQTT) and remote sensors (SensorMQTT)
"""

import asyncio

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

class PlatformMQTT(object):

    def __init__(self, settings=None):
        print("PlatformMQTT __init__()")
        self.settings = settings
        self.client = MQTTClient()

    async def start(self):
        print('start() startup')
        await self.client.connect(self.settings["PLATFORM_HOST"])
        print('start() connected {}'.format(self.settings["PLATFORM_HOST"]))

    async def send(self, topic, message=None):
        print('PlatformMQTT send() sending {}'.format(topic))
        message_b = bytes(message,'utf-8')
        tasks = [
            asyncio.ensure_future(self.client.publish(topic, message_b))
        ]
        await asyncio.wait(tasks)
        print("PlatformMQTT send() published {} {}".format(topic,message))

    async def finish(self):
        await self.client.disconnect()

class SensorMQTT(object):
    """
    SensorMQTT provides the local communications endpoint for receiving
    data from the remote sensors within the SensorNode
    """

    def __init__(self, settings=None, topic=None):
        print("SensorMQTT __init__() {}".format(topic))
        self.settings = settings
        self.topic = topic

    async def start(self):
        print("SensorMQTT start() {}".format(self.topic))
        self.client = MQTTClient(config=None)

        await self.client.connect(self.settings["SENSOR_HOST"])
        print("SensorMQTT {} connected".format(self.topic))

        await self.client.subscribe([(self.topic, QOS_0)])
        print("SensorMQTT {} subscribed".format(self.topic))

    async def get(self):
        return await self.client.deliver_message()

    async def finish(self):
        await self.client.disconnect()
        print("remote_sensor {} disconnected".format(self.topic))
