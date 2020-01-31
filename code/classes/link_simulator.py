"""
SensorNode link simulator

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

class LinkSimulator(object):

    def __init__(self, settings=None):
        print("Using LinkSimulator")
        self.settings = settings

        self.subscription_queue = asyncio.Queue()
        print("LinkSimulator __init__ completed")


    async def start(self, server_settings):
        """
        Connects to broker
        """
        print('LinkSimulator.start() startup')
        self.message_loop = True
        print('LinkSimulator.start() connected {}'.format(server_settings["host"]))


    async def put(self, sensor_id, event):
        """
        Sends sensor_id/event to MQTT broker.
        sensor_id is string, used as MQTT topic
        event is dictionary which will be converted to bytes for MQTT message
        """
        print('LinkSimulator.put() sending {}'.format(sensor_id))
        print("LinkSimulator.put() published {} {}".format(sensor_id,event))


    async def subscribe(self, subscribe_settings):
        """
        Subscribes to sensor events.
        """
        print("LinkSimulator.subscribed() {}".format(subscribe_settings["topic"]))

        asyncio.ensure_future(self.sim_messages())


    async def get(self):
        print("LinkSimulator get requested from client, awaiting queue")
        message = await self.subscription_queue.get()
        print("LinkSimulator get returned from queue")

        return message

    # Put a message in the queue every 10 seconds
    async def sim_messages(self):
        topic = "/csn-node-test-brew/tele/SENSOR"
        self.message_loop = True
        while self.message_loop:
            await asyncio.sleep(10)
            message_dict = {"Time":"2020-01-30T02:12:47",
                            "ENERGY":{"TotalStartTime":"2019-12-28T13:42:45",
                                      "Total":2.489,
                                      "Yesterday":0.877,
                                      "Today":0.003,
                                      "Period":0,
                                      "Power":2,
                                      "ApparentPower":9,
                                      "ReactivePower":9,
                                      "Factor":0.18,
                                      "Voltage":246,
                                      "Current":0.035},
                            "topic":"csn-node-test-brew/tele/SENSOR"}
            print('LinkSimulator RECV MSG:', topic)
            self.subscription_queue.put_nowait(message_dict)
        print("LinkSimulator message loop finished")


    async def finish(self):
        self.message_loop = False
        print("LinkSimulator finished")

