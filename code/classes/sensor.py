# Python libs
import time
import sys
import simplejson as json
import requests
import math

GPIO_FAIL = False
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO_FAIL = True
    print("RPi.GPIO not loaded, running in SIMULATION_MODE")

# General utility function (like list_to_string)
from classes.sensor_utils import list_to_string

from classes.time_buffer import TimeBuffer, StatsBuffer

from classes.display import Display

from classes.events import Events

VERSION = "SENSOR_0.70"

# Data for pattern recognition

DEFAULT_SIZE = 1000 # Sample history size if not in settings "SAMPLE_BUFFER_SIZE"
EVENT_HISTORY_SIZE = 1000 # keep track of the most recent 1000 events sent to server (since reboot)
STATS_HISTORY_SIZE = 1000 # Define a stats_buffer with 1000 entries, each 1 second long
STATS_DURATION = 1

debug_list = [ 1, 2, 3, 4] # weights from each load cell, for debug display on LCD

class Sensor(object):

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # __init__() called on startup
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def __init__(self, settings=None):
        global GPIO_FAIL

        self.SIMULATION_MODE = GPIO_FAIL

        self.settings = settings

        if self.settings is None:
            self.settings = { }

        if not "VERSION" in self.settings:
            self.settings["VERSION"] = VERSION

        if not "SAMPLE_BUFFER_SIZE" in self.settings:
            self.size = DEFAULT_SIZE
        else:
            self.size = settings["SAMPLE_BUFFER_SIZE"]

        # times to control watchdog sends to platform
        self.prev_send_time = None

        self.display = Display(self.settings, self.SIMULATION_MODE)

        # Create a 30-entry x 1-second stats buffer
        self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE, 
                                        duration=STATS_DURATION, 
                                        settings=self.settings)

        self.sample_buffer = TimeBuffer(size=self.size, settings=self.settings, stats_buffer=self.stats_buffer )

        self.event_buffer = TimeBuffer(size=EVENT_HISTORY_SIZE, settings=self.settings)

        self.events = Events(settings=self.settings, 
                             sample_buffer=self.sample_buffer,
                             event_buffer=self.event_buffer,
                             stats_buffer=self.stats_buffer
                            )

    # -----------------
    # Start sensor
    # -----------------

    def begin(self):
        # set counter for how many samples to collect before saving
        if self.settings is None or not "SAMPLE_SAVE_COUNT" in self.settings:
            self.save_count = 0
        else:
            self.save_count = self.settings["SAMPLE_SAVE_COUNT"]
        self.save_counter = 0 # cumulative count of how many samples we've collected
        print("Set save_count to", self.save_count)

        self.display.begin()


    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # SEND DATA TO PLATFORM
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Post data to platform as json.
    # post_data is a python dictionary to be converted to json.
    def send_data(self, post_data):
        try:
            print("send_data() to {}".format(self.settings["FEEDMAKER_URL"]))
            if not self.SIMULATION_MODE:
                response = requests.post(
                        self.settings["FEEDMAKER_URL"],
                        headers={ self.settings["FEEDMAKER_HEADER_KEY"] : self.settings["FEEDMAKER_HEADER_VALUE"] },
                        json=post_data
                        )
                print("status code:",response.status_code)

            debug_str = json.dumps( post_data,
                                    sort_keys=True,
                                    indent=4,
                                    separators=(',', ': '))
            print("sent:\n {}".format(debug_str))
        except Exception as e:
            print("send_data() error with {}".format(post_data))
            print(e)

    def send_weight(self, ts, weight_g):
        post_data = {  'msg_type': 'coffee_pot_weight',
                    'request_data': [ { 'acp_id': self.settings["SENSOR_ID"],
                                        'acp_type': self.settings["SENSOR_TYPE"],
                                        'acp_ts': ts,
                                        'acp_units': 'GRAMS',
                                        'weight': math.floor(weight_g+0.5), # rounded to integer grams
                                        'version': self.settings["VERSION"]
                                        }
                                    ]
                }
        self.send_data(post_data)

    def send_event(self, ts, event_data):

        message_data = { 'acp_id': self.settings["SENSOR_ID"],
                         'acp_type': self.settings["SENSOR_TYPE"],
                         'acp_ts': ts,
                         'version': self.settings["VERSION"]
                       }

        # merge dictionaries
        message_data = { **message_data, **event_data }

        post_data = { 'msg_type': 'coffee_pot_event',
                    'request_data': [ message_data ]
                }
        self.send_data(post_data)

    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    #
    # process_sample(timestamp, value)
    #
    # Here is where we process each sensor sample, updating the LCD and checking for events
    #
    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    def process_sample(self, ts, value):

        t_start = time.process_time()

        if self.settings["LOG_LEVEL"] == 1:
            print("process_sample got value {:.1f} at {:.3f} secs.".format(value, time.process_time() - t_start))

        # store weight and time in sample_history
        self.sample_buffer.put(ts, value)

        if self.save_count > 0:
            self.save_counter += 1
            if self.save_counter >= self.save_count:
                self.sample_buffer.save("../data/save_{:.3f}.csv".format(time.time()))
                self.save_counter = 0

        # ---------------------------------
        # TEST EVENTS AND SEND TO PLATFORM
        # ---------------------------------

        events_now = self.events.test(ts, value)

        for event in events_now:
            self.event_buffer.put(ts, event)
            if event["event_code"] == self.events.EVENT_NEW:
                self.display.update_new(ts)
            self.send_event(ts, event)
 
        #----------------
        # UPDATE DISPLAY
        # ---------------

        self.display.update(ts, self.sample_buffer, debug_list)


        # ------------------------------------------
        # SEND 'WATCHDOG' (WITH WEIGHT) TO PLATFORM
        # ------------------------------------------

        if self.prev_send_time is None:
            self.prev_send_time = ts

        WATCHDOG_PERIOD = 120
        if ts - self.prev_send_time > WATCHDOG_PERIOD:
            sample_value, offset, duration, sample_count = self.sample_buffer.median(0,2) # from latest ts, back 2 seconds

            if not sample_value == None:
                print ("SENDING WEIGHT {:5.1f}, {}".format(sample_value, time.ctime(ts)))

                self.send_weight(ts, sample_value)

                self.prev_send_time = ts

                if self.settings["LOG_LEVEL"] == 1:
                    print("process_sample send data at {:.3f} secs.".format(time.process_time() - t_start))
            else:
                print("process_sample send data NOT SENT as data value None")

        if self.settings["LOG_LEVEL"] == 1:
            print ("WEIGHT {:5.1f}, {}".format(value, time.ctime(ts)))

        if self.settings["LOG_LEVEL"] == 1:
            print("process_sample time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # finish() - cleanup and exit if main loop is interrupted
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def finish(self):
        print("\n")

        if not self.SIMULATION_MODE:

            self.display.finish()

            print("GPIO cleanup()...")

            GPIO.cleanup()

            print("Exitting")

            sys.exit()

