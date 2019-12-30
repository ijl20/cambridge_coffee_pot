import logging
import asyncio
import time
import random
import simplejson as json

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from classes.time_buffer import TimeBuffer

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

async def remote_event_detect(uplink_client, sample_buffer, event_buffer):
    value = sample_buffer.get(0)

    #debug send event for every message from remote sensors
    if True:
        remote_event = {   "acp_ts": time.time(),
                           "acp_id": "csn-node-test",
                           "event_code": "COFFEE_REMOTE",
                           "event_value": value
                       }

        remote_msg = json.dumps(remote_event)

        await uplink_send(uplink_client, "csn-node-test", remote_msg)


async def remote_sensors(uplink_client, event_buffer):
    print('remote_sensors() startup')

    sample_buffer = TimeBuffer(100)

    sensor_client = MQTTClient('csn-node-test')
    await sensor_client.connect('mqtt://localhost')
    await sensor_client.subscribe([
            ('csn-node-test-a/#', QOS_0),
            ('csn-node-test-b/#', QOS_0)
         ])
    try:
        while True:
            message = await sensor_client.deliver_message()
            packet = message.publish_packet

            if packet.payload is None:
                print("remote_sensors packet.payload=None {}".format(packet.variable_header.topic_name))
            elif packet.payload.data is None:
                print("remote_sensors() packet.payload.data=None {}".format(packet.variable_header.topic_name))
            else:
                print("remote_sensors() {} => {}".format(packet.variable_header.topic_name,
                                                          packet.payload.data))

                                                          ##DEBUG BUG HERE BYTES->STRING
            sample_buffer.put(time.time(), json.loads(packet.payload.data))
            await remote_event_detect(uplink_client, sample_buffer, event_buffer)

    except ClientException as client_exception:
        print("remote_sensors() Client exception: {}".format(client_exception))

    await sensor_client.unsubscribe([
        ('csn-node-test-a/#'),
        ('csn-node-test-b/#')
    ])

    await sensor_client.disconnect()

async def local_event_detect(uplink_client, sample_buffer, event_buffer):
    sample = sample_buffer.get(0)

    if not sample is None and sample["value"] > 99:
        watchdog_event = { "acp_ts": time.time(),
                           "acp_id": "csn-node-test",
                           "event_code": "COFFEE_WATCHDOG",
                           "event_value": sample["value"]
                         }

        watchdog_msg = json.dumps(watchdog_event)

        await uplink_send(uplink_client, "csn-node-test", watchdog_msg)

async def local_sensor(uplink_client, event_buffer):

    sample_buffer = TimeBuffer(1000)

    startup_event = { "acp_ts": time.time(),
                      "acp_id": "csn-node-test",
                      "event_code": "COFFEE_STARTUP"
                    }

    startup_msg = json.dumps(startup_event)

    await uplink_send(uplink_client, "csn-node-test", startup_msg)

    quit = False
    while not quit:
        rand = random.random() * 100
        sample_buffer.put(time.time(), rand)
        await local_event_detect(uplink_client, sample_buffer, event_buffer)
        await asyncio.sleep(0.1)

async def main():
    event_buffer = TimeBuffer(100)
    uplink_client = await uplink_init()
    await asyncio.gather(local_sensor(uplink_client,event_buffer),
                         remote_sensors(uplink_client, event_buffer))


if __name__ == '__main__':
    print('hbmqtt startup')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
