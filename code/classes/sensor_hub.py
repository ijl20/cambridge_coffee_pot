"""
The SensorHub .test() method is called every time new data is available from any of the
connected sensors. An event will be sent via the PlatformMQTT to the Platform when appropriate.
"""
import simplejson as json
from simplejson.errors import JSONDecodeError
import time
import math

from classes.links_hbmqtt import PlatformMQTT as Uplink
from classes.display import Display
from classes.events import Events

class SensorHub(object):
    """
    The SensorHub object provides a .process_reading() function that looks
    at the values in the various sensor buffers and
    decides whether an event should be sent to the platform.
    """

    def __init__(self, settings=None):
        print("SensorHub __init()__")
        self.settings = settings

        # LCD DISPLAY

        self.display = Display(self.settings)

        self.display.begin()

        # EVENTS PATTERN MATCH

        self.events = Events(settings=self.settings)

        # Connect to the platform
        self.uplink = Uplink(settings=self.settings)

        # times to control periodic sends to platform
        self.prev_send_time = None


    # A LocalSensor or RemoteSensor will call this add_buffers() method to
    # make their TimeBuffers visible to Events
    def add_buffers(self, sensor_id, buffers):
        print("SensorHub adding buffers for {}: {}".format(sensor_id,buffers))
        self.events.sensor_buffers[sensor_id] = buffers

    # start() is async to allow Uplink.send
    async def start(self, ts):
        await self.uplink.start()

        # Send startup message
        startup_event = { "acp_ts": ts,
                          "acp_id": self.settings["SENSOR_ID"],
                          "event_code": self.events.EVENT_STARTUP
                        }

        startup_msg = json.dumps(startup_event)

        #send MQTT topic, message
        await self.uplink.send(self.settings["SENSOR_ID"], startup_msg)

    #debug still to be implemented
    # watchdog is called by Watchdog coroutine periodically
    async def watchdog(self):
        print("{:.3f} SensorHub() watchdog...".format(time.time()))

    # send 'weight' event (periodic)
    async def send_weight(self, ts, weight_g):
        weight_event = { 'acp_id': self.settings["SENSOR_ID"],
                         'acp_type': self.settings["SENSOR_TYPE"],
                         'acp_ts': ts,
                         'acp_units': 'GRAMS',
                         'event_code': self.events.EVENT_WEIGHT,
                         'weight': math.floor(weight_g+0.5), # rounded to integer grams
                         'version': self.settings["VERSION"]
                       }

        weight_msg = json.dumps(weight_event)

        #send MQTT topic, message
        await self.uplink.send(self.settings["SENSOR_ID"], weight_msg)

    async def process_reading(self, ts, sensor_id):
        t_start = time.process_time()

        # ---------------------------------
        # TEST EVENTS AND SEND TO PLATFORM
        # ---------------------------------
        events_list = self.events.test(ts, sensor_id)

        for event in events_list:
            # display time of new brew is we have one
            if event["event_code"] == self.events.EVENT_NEW:
                self.display.update_new(ts)

            # add acp_id, acp_ts, acp_type
            event_params =  { "acp_ts": ts,
                              "acp_id": self.settings["SENSOR_ID"],
                              "acp_type": self.settings["SENSOR_TYPE"]
                            }
            #send MQTT topic, message
            event_msg = json.dumps({ **event, **event_params })

            await self.uplink.send(self.settings["SENSOR_ID"], event_msg)

        #----------------
        # UPDATE DISPLAY
        # ---------------

        weight_sample_buffer = self.events.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]
        self.display.update(ts, weight_sample_buffer)

        # ------------------------------------------
        # SEND 'WATCHDOG' (WITH WEIGHT) TO PLATFORM
        # ------------------------------------------

        if self.prev_send_time is None:
            self.prev_send_time = ts

        WATCHDOG_PERIOD = 120
        if ts - self.prev_send_time > WATCHDOG_PERIOD:
            sample_value, offset, duration, sample_count = weight_sample_buffer.median(0,2) # from latest ts, back 2 seconds

            if not sample_value == None:
                print ("{:.3f},{:5.1f},WEIGHT,".format(ts, sample_value), "{}".format(time.ctime(ts)))

                await self.send_weight(ts, sample_value)

                self.prev_send_time = ts

                if self.settings["LOG_LEVEL"] == 1:
                    print("process_sample send data at {:.3f} secs.".format(time.process_time() - t_start))
            else:
                print("process_sample send data NOT SENT as data value None")

        if self.settings["LOG_LEVEL"] == 1:
            print ("WEIGHT {:5.1f}, {}".format(weight_sample_buffer.get(0)["value"], time.ctime(ts)))

        if self.settings["LOG_LEVEL"] == 1:
            print("process_sample time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))


    async def finish(self):

        await self.uplink.finish()

        if not self.settings["DISPLAY_SIMULATION_MODE"]:

            self.display.finish()


