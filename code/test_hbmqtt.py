import logging
import asyncio
import time
import random

import simplejson as json
from simplejson.errors import JSONDecodeError

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from classes.time_buffer import TimeBuffer

settings = {
    "UPLINK_HOST": 'mqtt://192.168.1.51',
    "SENSOR_ID": "csn-node-test"
}

class Uplink(object):

    def __init__(self):
        print("Uplink __init__()")

    async def start(self):
        print('start() startup')
        self.client = MQTTClient()
        await self.client.connect(settings["UPLINK_HOST"])
        print('start() connected {}'.format(settings["UPLINK_HOST"]))

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

async def remote_event_detect(uplink, sample_buffer, event_buffer):
    value = sample_buffer.get(0)

    #debug send event for every message from remote sensors
    if True:
        remote_event = {   "acp_ts": time.time(),
                           "acp_id": settings["SENSOR_ID"],
                           "event_code": "COFFEE_REMOTE",
                           "event_value": value
                       }

        remote_msg = json.dumps(remote_event)

        await uplink.send(settings["SENSOR_ID"], remote_msg)

async def remote_sensors(uplink, event_buffer):
    print('remote_sensors() startup')

    sample_buffer = TimeBuffer(100)

    sensor_client = MQTTClient(settings["SENSOR_ID"])
    await sensor_client.connect('mqtt://localhost')
    await sensor_client.subscribe([
            (settings["SENSOR_ID"]+"-a/#", QOS_0),
            (settings["SENSOR_ID"]+"-b/#", QOS_0)
         ])
    try:
        while True:
            message_obj = await sensor_client.deliver_message()
            packet = message_obj.publish_packet
            topic = packet.variable_header.topic_name

            print("remote_sensors() topic received {}".format(topic))

            message = ""
            if packet.payload is None:
                print("remote_sensors packet.payload=None {}".format(topic))
            elif packet.payload.data is None:
                print("remote_sensors() packet.payload.data=None {}".format(topic))
            else:
                message = packet.payload.data.decode('utf-8')
                print("remote_sensors() {} => {}".format(topic,message))

            message_dict = {}
            try:
                message_dict = json.loads(message)
            except JSONDecodeError:
                message_dict["message"] = message
                print("remote_sensors() json msg error: {} => {}".format(topic,message))

            message_dict["topic"] = topic

            sample_buffer.put(time.time(), message_dict)

            await remote_event_detect(uplink, sample_buffer, event_buffer)

    except ClientException as client_exception:
        print("remote_sensors() Client exception: {}".format(client_exception))

    await sensor_client.unsubscribe([
        (settings["SENSOR_ID"]+"-a/#"),
        (settings["SENSOR_ID"]+"-b/#")
    ])

    print("remote_sensors() unsubscribed")

    await sensor_client.disconnect()

    print("remote_sensors disconnected()")

async def local_event_detect(uplink, sample_buffer, event_buffer):
    sample = sample_buffer.get(0)

    if not sample is None and sample["value"] > 99:
        watchdog_event = { "acp_ts": time.time(),
                           "acp_id": settings["SENSOR_ID"],
                           "event_code": "COFFEE_WATCHDOG",
                           "event_value": sample["value"]
                         }

        watchdog_msg = json.dumps(watchdog_event)

        await uplink.send(settings["SENSOR_ID"], watchdog_msg)

async def local_sensor(uplink, event_buffer):

    sample_buffer = TimeBuffer(1000)

    startup_event = { "acp_ts": time.time(),
                      "acp_id": settings["SENSOR_ID"],
                      "event_code": "COFFEE_STARTUP"
                    }

    startup_msg = json.dumps(startup_event)

    await uplink.send(settings["SENSOR_ID"], startup_msg)

    quit = False
    while not quit:
        rand = random.random() * 100
        sample_buffer.put(time.time(), rand)
        await local_event_detect(uplink, sample_buffer, event_buffer)
        await asyncio.sleep(0.1)

async def main():
    event_buffer = TimeBuffer(100)
    uplink = Uplink()
    await uplink.start()
    await asyncio.gather(local_sensor(uplink,event_buffer),
                         remote_sensors(uplink, event_buffer))


if __name__ == '__main__':
    print('hbmqtt startup')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
