# -------------------------------------------------------------------
#
# Python script to run sensor
#
# -------------------------------------------------------------------

import sys
import time
import asyncio
import signal

# Async MQTT
from gmqtt.mqtt.constants import MQTTv311
from gmqtt import Client as MQTTClient

from classes.sensor import Sensor

from classes.weight_sensor import WeightSensor

from classes.config import Config

from classes.sensor_utils import list_to_string

VERSION = "0.80"

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Class Comms
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

class Comms(object):

    def __init__(self, handle_input):
        print("Comms init()")

        self.handle_input = handle_input

        self.STOP = asyncio.Event()

        self.client = MQTTClient("client-id")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe


    async def begin(self, broker_host, broker_port):

        #client.set_auth_credentials(token, None)
        await self.client.connect(broker_host, broker_port, version=MQTTv311)

        self.client.publish('TEST/TIME', str(time.time()), qos=1)

    async def finish(self):

        #await self.STOP.wait()
        await self.client.disconnect()

    def on_connect(self, client, flags, rc, properties):
        print('Connected')
        self.client.subscribe('TEST/#', qos=0)


    def on_message(self, client, topic, payload, qos, properties):
        self.handle_input(payload)


    def on_disconnect(self, client, packet, exc=None):
        print('Disconnected')

    def on_subscribe(self, client, mid, qos):
        print('SUBSCRIBED')

    def ask_exit(self, *args):
        self.STOP.set()

def handle_input(input):
    print("got input",input)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

async def main():

    print("main started with {} arguments {}".format(len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    config.settings["VERSION"] = VERSION

    comms = Comms(handle_input)

    await comms.begin('localhost', 1887)

    s = Sensor(settings = config.settings)

    weight_sensor = WeightSensor(config.settings)

    s.begin()

    # Infinite loop until killed, reading weight and sending data
    try:
        while True:
            loop_start_time = time.time()

            #----------------
            # GET READING
            # ---------------

            # get readings from all load cells
            value = weight_sensor.get_value()

            # ---------------
            # PROCESS READING
            # ---------------
            s.process_sample(time.time(), value)

            loop_time = time.time() - loop_start_time
            if loop_time < 0.1:
                await asyncio.sleep(0.1 - loop_time)

    except (KeyboardInterrupt, SystemExit):
        pass

    # Cleanup and quit
    s.finish()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    #loop.add_signal_handler(signal.SIGINT, ask_exit)
    #loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main())
