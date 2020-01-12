"""
MQTT links to Platform (PlatformMQTT) and remote sensors (SensorMQTT)

link = Link(settings) - instantiate object. settings = application settings e.g. "LOG_LEVEL"

await link.start(server_settings) - CONNECT to host, server_settings e.g. "host"

await link.finish() - cleanup, e.g. DISCONNECT from host

await link.put(sensor_id, event) - SENDS message to host

await link.subscribe(sensor_id) - requests SUBSCRIPTION from host

await link.get() - async GETS next message from host

"""

import asyncio
import simplejson as json

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

class LinkHBMQTT(object):

    def __init__(self, settings=None):
        print("LinkHBMQTT __init__()")
        self.settings = settings
        self.client = MQTTClient()

    async def start(self, server_settings):
        print('LinkHBMQTT.start() startup')
        await self.client.connect("mqtt://"+server_settings["host"])
        print('LinkHBMQTT.start() connected {}'.format(server_settings["host"]))

    async def put(self, sensor_id, event):
        """
        Sends sensor_id/event to MQTT broker.
        sensor_id is string, used as MQTT topic
        event is dictionary which will be converted to bytes for MQTT message
        """
        print('LinkHBMQTT.put() sending {}'.format(sensor_id))

        message = json.dumps(event)

        message_b = bytes(message,'utf-8')
        tasks = [
            asyncio.ensure_future(self.client.publish(sensor_id, message_b))
        ]
        await asyncio.wait(tasks)
        print("LinkHBMQTT.put() published {} {}".format(sensor_id,message))

    async def subscribe(self, subscribe_settings):
        await self.client.subscribe([(subscribe_settings["topic"], QOS_0)])
        print("LinkHBMQTT.subscribed() {}".format(subscribe_settings["topic"]))

    async def get(self):
        return await self.client.deliver_message()

    async def finish(self):
        await self.client.disconnect()

