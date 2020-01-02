"""
The SensorHub .test() method is called every time new data is available from any of the
connected sensors. An event will be sent via the PlatformMQTT to the Platform when appropriate.
"""
import simplejson as json
from simplejson.errors import JSONDecodeError

from classes.links import PlatformMQTT as Uplink

from classes.events import Events

class SensorHub(object):
    """
    The SensorHub object provides a .process_reading() function that looks at the values in the various sensor buffers and
    decides whether an event should be sent to the platform.
    """

    def __init__(self, settings=None):
        print("SensorHub __init()__")
        self.settings = settings

        self.events = Events(settings=self.settings)

        # Connect to the platform
        self.uplink = Uplink(settings=self.settings)

    # A LocalSensor or RemoteSensor will call this add_buffers() method to make their TimeBuffers visible to Events
    def add_buffers(self, sensor_id, buffers):
        print("Adding Event buffers for {}: {}".format(sensor_id,buffers))
        self.events.sensor_buffers[sensor_id] = buffers

    # start() is async to allow Uplink.send
    async def start(self, ts):
        await self.uplink.start()

        # Send startup message
        startup_event = { "acp_ts": ts,
                          "acp_id": self.settings["SENSOR_ID"],
                          "event_code": "COFFEE_STARTUP"
                        }

        startup_msg = json.dumps(startup_event)

        #send MQTT topic, message
        await self.uplink.send(self.settings["SENSOR_ID"], startup_msg)

    #debug still to be implemented
    # watchdog is called by Watchdog coroutine periodically
    async def watchdog(self):
        print("watchdog")

    async def process_reading(self, ts, sensor_id):
        events_list = self.events.test(ts, sensor_id)

        for event in events_list:
            #send MQTT topic, message
            event_msg = json.dumps(event)
            await self.uplink.send(self.settings["SENSOR_ID"], event_msg)
