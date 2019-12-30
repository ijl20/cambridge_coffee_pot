import logging
import asyncio
import time
import random

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

UPLINK_HOST = 'mqtt://192.168.1.51'

async def uplink_init():
    print('uplink_init() startup')
    uplink_client = MQTTClient()
    await uplink_client.connect(UPLINK_HOST)
    print('uplink_init() connected {}'.format(UPLINK_HOST))
    return uplink_client

async def uplink_send(uplink_client, topic, message=None):
    print('uplink_send() sending {} {}'.format(topic,message))
    #topic_b = bytes(topic,'utf-8')
    message_b = bytes(message,'utf-8')
    tasks = [
        asyncio.ensure_future(uplink_client.publish(topic, message_b))
    ]
    await asyncio.wait(tasks)
    print("uplink_send() published {} {}".format(topic,message))

async def uplink_finish():
    await uplink_client.disconnect()

async def remote_coro():
    print('remote_coro() startup')
    sensor_client = MQTTClient('csn-node-test')
    await sensor_client.connect('mqtt://localhost')
    await sensor_client.subscribe([
            ('csn-node-test-a/#', QOS_0),
            ('csn-node-test-b/#', QOS_0)
         ])
    try:
        for i in range(1, 10):
            message = await sensor_client.deliver_message()
            packet = message.publish_packet
            print("{}:  {} => {}".format(i,
                                         packet.variable_header.topic_name,
                                         str(packet.payload.data)))
        await sensor_client.unsubscribe([
            ('csn-node-test-a/#'),
            ('csn-node-test-b/#')
        ])
        await sensor_client.disconnect()
    except ClientException as client_exception:
        print("remote_coro() Client exception: {}".format(client_exception))

async def sensor_loop():

    uplink_client = await uplink_init()

    await uplink_send(uplink_client, "csn-node-test/status","startup")

    quit = False
    while not quit:
        rand = random.random() * 100
        if rand > 95:
            await uplink_send(uplink_client,
                              "csn-node-test/COFFEE_WATCHDOG",
                              "{:.1f}".format(rand))
        await asyncio.sleep(0.1)

async def main():
    await asyncio.gather(sensor_loop(), remote_coro())


if __name__ == '__main__':
    print('hbmqtt startup')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
