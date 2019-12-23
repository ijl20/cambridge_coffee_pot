
import asyncio
import signal
import time

# Async MQTT
from gmqtt.mqtt.constants import MQTTv311
from gmqtt import Client as MQTTClient

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Class SmartPlug
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

class SmartPlug(object):

    def __init__(self, sensor_id=None, event_buffer=None, settings=None):
        print("SmartPlug init()",sensor_id)

        #debug will put these in settings
        self.broker_host = '192.168.1.51'
        self.broker_port = 1883

        self.sensor_id = sensor_id

        self.STOP = asyncio.Event()

        self.client = MQTTClient(self.sensor_id+"_node")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe


    async def begin(self):

        #client.set_auth_credentials(token, None)
        await self.client.connect(self.broker_host, self.broker_port, version=MQTTv311)

    async def finish(self):

        #await self.STOP.wait()
        await self.client.disconnect()

    def on_connect(self, client, flags, rc, properties):
        print('{} Connected to {}'.format(self.sensor_id, self.broker_host+':'+str(self.broker_port)))

        #print("{} Publishing".format(self.sensor_id))
        #self.client.publish('TEST/TIME', "{:.3f} {} {}".format(time.time(),self.sensor_id,'connected mqtt'), qos=1)

        subscribe_str = 'CSN_NODE/tele/{}/SENSOR'.format(self.sensor_id)
        print("{} Subscribing to {}".format(self.sensor_id, subscribe_str))
        self.client.subscribe(subscribe_str, qos=0)

    def on_message(self, client, topic, payload, qos, properties):
        self.handle_input(payload)

    def on_disconnect(self, client, packet, exc=None):
        print('{} Disconnected'.format(self.sensor_id))

    def on_subscribe(self, client, mid, qos):
        print("{} Subscribed".format(self.sensor_id))

    def ask_exit(self, *args):
        self.STOP.set()

    def handle_input(self, input):
        print("{} got input {}".format(self.sensor_id,input))
