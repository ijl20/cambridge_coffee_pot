"""
The SensorHub, instantiated by a SensorNode with s = SensorHub(settings):
* the SensorNode will also instantiate LocalSensors and RemoteSensors, passing the SensorHub to them
* the LocalSensors and RemoteSensors will make their TimeBuffers visible to the SensorHub, and so to Events.
* the SensorHub will instantiate an Uplink for sending data to the Platform
* the SensorHub will instantiate an Events to test incoming date for patterns
* the SensorHub receives data from the LocalSensors and RemoteSensors
* on each data 'tick' the SensorHub calls the Events.test(ts,sensor_id) method
* Events will be sent via the Uplink to the Platform when appropriate.
"""
import simplejson as json
from simplejson.errors import JSONDecodeError
import time
import math

from classes.link_simulator import LinkSimulator
#from classes.link_hbmqtt import LinkHBMQTT as Uplink
from classes.link_gmqtt import LinkGMQTT as Uplink
from classes.display import Display
from classes.events import Events, EventCode

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
        if ( "SIMULATE_UPLINK" in self.settings and
             self.settings["SIMULATE_UPLINK"]):
            self.uplink = LinkSimulator(settings=self.settings)
        else:
            self.uplink = Uplink(settings=self.settings)

        # times to control periodic sends to platform
        self.prev_send_time = None


    # A LocalSensor or RemoteSensor will call this add_buffers() method to
    # make their TimeBuffers visible to Events
    def add_buffers(self, sensor_id, buffers):
        print("SensorHub adding buffers for {}".format(sensor_id))
        self.events.sensor_buffers[sensor_id] = buffers

    # start() is async to allow Uplink.send
    async def start(self, ts):

        uplink_settings = {}
        uplink_settings["host"] = self.settings["PLATFORM_HOST"]
        uplink_settings["port"] = self.settings["PLATFORM_PORT"]
        uplink_settings["user"] = self.settings["PLATFORM_USER"]
        uplink_settings["password"] = self.settings["PLATFORM_PASSWORD"]

        await self.uplink.start(uplink_settings)

        # Send startup message
        startup_event = { "acp_ts": ts,
                          "acp_id": self.settings["SENSOR_ID"],
                          "event_code": EventCode.STARTUP
                        }

        #send to platform
        await self.uplink.put(self.settings["SENSOR_ID"], startup_event)

    #debug still to be implemented
    # watchdog is called by Watchdog coroutine periodically
    async def watchdog(self):
        print("{:.3f} SensorHub() watchdog...".format(time.time()))

    # send 'status' event (periodic)
    async def send_status(self, ts, weight_g):
        weight_event = { 'acp_id': self.settings["SENSOR_ID"],
                         'acp_type': self.settings["SENSOR_TYPE"],
                         'acp_ts': ts,
                         'acp_units': 'GRAMS',
                         'event_code': EventCode.STATUS,
                         'weight': math.floor(weight_g+0.5), # rounded to integer grams
                         'version': self.settings["VERSION"]
                       }

        #send MQTT topic, message
        await self.uplink.put(self.settings["SENSOR_ID"], weight_event)

    # process_reading(ts, sensor_id) is called by each of the sensors, i.e.
    # LocalSensors and RemoteSensors, each time they have a reading to be
    # processed.  The Events module can use 'sensor_id' to determine the
    # source of the reading.  All events sent to the Platform are labelled
    # with the sensor_id of the sensor node, not the individual sensor.
    async def process_reading(self, ts, sensor_id):
        t_start = time.process_time()

        weight_sensor_id = self.settings["WEIGHT_SENSOR_ID"]

        # ---------------------------------
        # TEST EVENTS AND SEND TO PLATFORM
        # ---------------------------------
        events_list = self.events.test(ts, sensor_id)

        for event in events_list:
            # display time of new brew is we have one
            if event["event_code"] == EventCode.NEW:
                self.display.update_new(ts)

            # add acp_id, acp_ts, acp_type
            event_params =  { "acp_ts": ts,
                              "acp_id": self.settings["SENSOR_ID"],
                              "acp_type": self.settings["SENSOR_TYPE"]
                            }
            #send MQTT topic, message
            event_to_send = { **event, **event_params }

            await self.uplink.put(self.settings["SENSOR_ID"], event_to_send)

            self.display.update_event(ts, event)

        #----------------
        # UPDATE DISPLAY
        # ---------------

        weight_sample_buffer = self.events.sensor_buffers[weight_sensor_id]["sample_buffer"]
        self.display.update(ts, weight_sample_buffer)

        # ------------------------------------------
        # SEND 'WATCHDOG' (WITH WEIGHT) TO PLATFORM
        # ------------------------------------------

        if self.prev_send_time is None:
            self.prev_send_time = ts

        WATCHDOG_PERIOD = 120
        if ts - self.prev_send_time > WATCHDOG_PERIOD:
            # from latest ts, back 2 seconds
            sample_value, offset, duration, sample_count = weight_sample_buffer.median(0,2)

            if not sample_value == None:
                print ("{:.3f} WEIGHT {:5.1f}".format(ts, sample_value))

                await self.send_status(ts, sample_value)

                self.prev_send_time = ts

                if self.settings["LOG_LEVEL"] == 1:
                    print("process_reading send data at {:.3f} secs.".format(time.process_time() - t_start))
            else:
                print("process_reading send data NOT SENT as data value None")

        if self.settings["LOG_LEVEL"] == 1:
            print ("WEIGHT,{:.3f},{:.3f}".format(ts,weight_sample_buffer.get(0)["value"]))

        if self.settings["LOG_LEVEL"] == 1:
            print("process_reading time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))


    async def finish(self):

        await self.uplink.finish()

        if not self.settings["SIMULATE_DISPLAY"]:

            self.display.finish()


