import asyncio
import os
import signal
import time

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

# gmqtt also compatibility with uvloop
#import uvloop
#asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


STOP = asyncio.Event()


def on_connect(client, flags, rc, properties):
    print('Connected')
    client.subscribe('#', qos=0)


def on_message(client, topic, payload, qos, properties):
    print('RECV MSG:', payload)


def on_disconnect(client, packet, exc=None):
    print('Disconnected')

def on_subscribe(client, mid, qos):
    print('SUBSCRIBED')

def ask_exit(*args):
    STOP.set()

async def main(broker_host, token):

    print("main started")

    client = MQTTClient(None)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    print("connecting")

    # client.set_auth_credentials(token, None)
    await client.connect(broker_host,version=MQTTv311)

    print("connected... publishing")

    client.publish('foo', str(time.time()), qos=1)

    print("published")

    await STOP.wait()
    await client.disconnect()

    print("finished")


if __name__ == '__main__':
    print("test_gmqtt start")

    loop = asyncio.get_event_loop()

    host = 'localhost'
    token = 'foo' # os.environ.get('FLESPI_TOKEN')

    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main(host, token))

