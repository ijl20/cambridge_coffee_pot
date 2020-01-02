"""
The SensorHub .test() method is called every time new data is available from any of the
connected sensors. An event will be sent via the Uplink to the Platform when appropriate.
"""

from classes.time_buffer import Timebuffer
from classes.links import Uplink

class SensorHub(object):
    """
    The SensorHub object provides a .test() function that looks at the values in the various sensor buffers and
    decides whether an event should be sent to the platform.
    """

    def __init__(self, settings=None):
        print("SensorHub __init()__")
        self.settings = settings

        # Create event buffer for sensor node, i.e. common to all sensors
        self.event_buffer = TimeBuffer(size=1000, settings=settings)

        # Create dictionary to reference buffers for each sensor
        # This Events object will be passed to each sensor __init__ so the sensor will add its buffers to sensor_buffers.
        self.sensor_buffers = {}

        # Connect to the platform
        self.uplink = Uplink(settings=self.settings)

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

    def test_event_remote(self, ts, sensor_id):
        # test if remote sensor (penultimate char = '-')
        if sensor_id[-2:-1] == "-":

            print("test_event_remote() {}".format(sensor_id))

            sample = self.sensor_buffers[sensor_id]["sample_buffer"].get(0)

            #debug send event for every message from remote sensors
            if True:
                remote_event = { "acp_ts": ts,
                                 "acp_id": sensor_id,
                                 "event_code": "COFFEE_REMOTE",
                                 "event_value": sample["value"]
                               }
                return remote_event

        return None

    def test_event_local(self, ts, sensor_id):
        if not sensor_id[-2:-1] == "-":
            sample = self.sensor_buffers[sensor_id]["sample_buffer"].get(0)

            if not sample is None and sample["value"] > 99:
                print("test_event_local() {}".format(sensor_id))
                local_event = { "acp_ts": ts,
                                "acp_id": sensor_id,
                                "event_code": "COFFEE_LOCAL",
                                "event_value": sample["value"]
                              }
                return local_event

        return None

    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    async def test(self, ts, sensor_id):
        events = []
        for test_function in [ self.test_event_remote,
                               self.test_event_local
                    ]:
            event = test_function(ts, sensor_id)
            if not event is None:
                events.append(event)

        for event in events:
            #send MQTT topic, message
            event_msg = json.dumps(event)
            await self.uplink.send(self.settings["SENSOR_ID"], event_msg)
