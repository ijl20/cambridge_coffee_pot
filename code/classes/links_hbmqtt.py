"""
MQTT links for SensorHub and RemoteSensors

link = Link(settings) - instantiate object. settings = application settings e.g. "LOG_LEVEL"

await link.start(server_settings) - CONNECT to host, server_settings e.g. "host"

await link.finish() - cleanup, e.g. DISCONNECT from host

await link.put(sensor_id, event) - SENDS message to host

await link.subscribe(subscription_settings) - requests SUBSCRIPTION from host, settings { topic: }

await link.get() - async GETS next message from host

"""

import asyncio
import simplejson as json
from simplejson.errors import JSONDecodeError

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

class LinkHBMQTT(object):

    def __init__(self, settings=None):
        print("LinkHBMQTT __init__()")
        self.settings = settings
        client_config = {
                            'keep_alive': 10,
                            'ping_delay': 1,
                            'default_qos': 0,
                            'default_retain': False,
                            'auto_reconnect': True,
                            'reconnect_max_interval': 5,
                            'reconnect_retries': 10000
                        }
        self.client = MQTTClient(config=client_config)

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
        if self.settings["LOG_LEVEL"] <= 2:
            print('LinkHBMQTT.put() sending {}'.format(sensor_id))

        message = json.dumps(event)

        message_b = bytes(message,'utf-8')
        tasks = [
            asyncio.ensure_future(self.client.publish(sensor_id, message_b))
        ]
        await asyncio.wait(tasks)
        if self.settings["LOG_LEVEL"] <= 2:
            print("LinkHBMQTT.put() published {} {}".format(sensor_id,message))

    async def subscribe(self, subscribe_settings):
        await self.client.subscribe([(subscribe_settings["topic"], QOS_0)])
        print("LinkHBMQTT.subscribed() {}".format(subscribe_settings["topic"]))

    async def get(self):
        message_obj = await self.client.deliver_message()
        packet = message_obj.publish_packet
        topic = packet.variable_header.topic_name

        if self.settings["LOG_LEVEL"] <= 2:
            print("LinkHBMQTT topic received {}".format(topic))

        message = ""
        if packet.payload is None:
            print("LinkHBMQTT packet.payload=None {}".format(topic))
        elif packet.payload.data is None:
            print("LinkHBMQTT packet.payload.data=None {}".format(topic))
        else:
            message = packet.payload.data.decode('utf-8')
            if self.settings["LOG_LEVEL"] <= 2:
                print("LinkHBMQTT {} => {}".format(topic,message))

        message_dict = {}
        try:
            message_dict = json.loads(message)
        except JSONDecodeError:
            message_dict["message"] = message
            print("LinkHBMQTT json msg error: {} => {}".format(topic,message))

        message_dict["topic"] = topic

        return message_dict        

    async def finish(self):
        await self.client.disconnect()

