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
    The SensorHub is created by a SensorNode and provides a
    .process_reading() function that looks
    at the values in the various sensor buffers and
    decides whether an event should be sent to the platform.
    """

    def __init__(self, settings=None):
        print("SensorHub __init()__")
        self.settings = settings

        self.new_status = None # timestamp, weight of current pot of coffee

        self.grind_status = None # most recent timestamp, power from grinder

        self.brew_status = None # most recent timestamp, power from brew machine

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


    # start() is async to allow Uplink.put
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
                          "acp_confidence": 1,
                          "event_code": EventCode.STARTUP
                        }

        #send to platform
        await self.uplink.put(self.settings["SENSOR_ID"], startup_event)

    # A LocalSensor or RemoteSensor will call this add_buffers() method to
    # make their TimeBuffers visible to Events
    # e.g. { "sample_buffer": self.sample_buffer,
    #        "stats_buffer": self.stats_buffer
    #      }
    def add_buffers(self, sensor_id, buffers):
        print("SensorHub adding buffers for {}".format(sensor_id))
        self.events.sensor_buffers[sensor_id] = buffers

    # watchdog is called by Watchdog coroutine periodically
    async def watchdog(self):
        ts = time.time()
        print("{:.3f} SensorHub() watchdog...".format(ts))
        # ------------------------------------------
        # SEND 'STATUS' (WITH WEIGHT) TO PLATFORM
        # ------------------------------------------
        weight_sensor_id = self.settings["WEIGHT_SENSOR_ID"]

        weight_sample_buffer = self.events.sensor_buffers[weight_sensor_id]["sample_buffer"]

        sample_value, offset, duration, sample_count = weight_sample_buffer.median(0,2)

        if not sample_value == None:
            print ("{:.3f} WEIGHT {:5.1f}".format(ts, sample_value))

            await self.send_status(ts, sample_value)

            if self.settings["LOG_LEVEL"] == 1:
                print("SensorHub.watchdog() send status at {:.3f}".format(time.process_time()))
        else:
            print("SensorHub.watchdog() status NOT SENT as data value None")


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

        # Add status (e.g. timestamp, weight) of latest brew if we have one
        if not self.new_status is None:
            weight_event["new_status"] = self.new_status

        # Add status (e.g. timestamp, power) of latest grind if we have one
        if not self.grind_status is None:
            weight_event["grind_status"] = self.grind_status

        # Add status (e.g. timestamp, power) of latest brewing if we have one
        if not self.brew_status is None:
            weight_event["brew_status"] = self.brew_status

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
        weight_sample_buffer = self.events.sensor_buffers[weight_sensor_id]["sample_buffer"]

        # ---------------------------------
        # TEST EVENTS AND SEND TO PLATFORM
        # ---------------------------------
        events_list = self.events.test(ts, sensor_id)

        for event in events_list:
            # display time of new brew is we have one

            event_code = event["event_code"]

            # If this event is a NEW POT then update display and record the time
            if event_code == EventCode.NEW:
                self.new_status = { "acp_ts": ts,
                                    "weight": event["weight"],
                                    "weight_new": event["weight_new"],
                                    "acp_confidence": event["acp_confidence"]
                                  }
                self.display.update_new(ts)

            # If this event is from the GRINDER then record the grind status for next COFFEE_STATUS event
            elif event_code == EventCode.GRINDING or event_code == EventCode.GRIND_STATUS:
                self.grind_status = { "acp_ts" : ts,
                                      "power": event["value"]["ENERGY"]["Power"],
                                      "acp_units": "WATTS"
                                    }
                # For a 'status' message from a RemoteSensor we only store it and return.
                if event_code == EventCode.GRIND_STATUS:
                    return

            # If this event is from the BREWER then record the brew status for the next COFFEE_STATUS event                                    
            elif event_code == EventCode.BREWING or event_code == EventCode.BREW_STATUS:
                self.brew_status = { "acp_ts" : ts,
                                     "power": event["value"]["ENERGY"]["Power"],
                                     "acp_units": "WATTS"
                                    }
                # For a 'status' message from a RemoteSensor we only store it and return.
                if event_code == EventCode.BREW_STATUS:
                    return
                                    
            # piggyback a weight property if the event doesn't already include it.
            if not "weight" in event:
                weight_stats_buffer = self.events.sensor_buffers[weight_sensor_id]["stats_buffer"]

                # we'll add a weight value for events that don't include it
                default_weight = weight_stats_buffer.get(0)["value"]["median"]

                if default_weight is None:
                    default_weight = 0

                event["weight"] = math.floor(default_weight+0.5)

            # also piggyback the timestamp of the most recent new brew
            if not self.new_status is None:
                event["new_status"] = self.new_status

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

        self.display.update(ts, weight_sample_buffer)

        if self.settings["LOG_LEVEL"] == 1:
            print ("WEIGHT,{:.3f},{:.3f}".format(ts,weight_sample_buffer.get(0)["value"]))

        if self.settings["LOG_LEVEL"] == 1:
            print("process_reading time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))


    async def finish(self):

        await self.uplink.finish()

        if not self.settings["SIMULATE_DISPLAY"]:

            self.display.finish()


