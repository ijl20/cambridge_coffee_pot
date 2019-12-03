#! /usr/bin/python3

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

# Data for pattern recognition

SAMPLE_HISTORY_SIZE = 1000
EVENT_HISTORY_SIZE = 5 # keep track of the most recent 5 events sent to server
STATS_HISTORY_SIZE = 30

# COFFEE POT EVENTS

EVENT_NEW = "COFFEE_NEW"
EVENT_EMPTY = "COFFEE_EMPTY"
EVENT_POURED = "COFFEE_POURED"
EVENT_REMOVED = "COFFEE_REMOVED"
EVENT_GROUND = "COFFEE_GROUND"

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

        # times to control watchdog sends to platform
        self.prev_send_time = None

        self.display = Display(self.settings, self.SIMULATION_MODE)

        # Create a 30-entry x 1-second stats buffer
        self.stats_buffer = StatsBuffer(size=STATS_HISTORY_SIZE, duration=1, settings=self.settings)

        self.sample_buffer = TimeBuffer(size=SAMPLE_HISTORY_SIZE, settings=self.settings, stats_buffer=self.stats_buffer )

        self.event_buffer = TimeBuffer(size=EVENT_HISTORY_SIZE, settings=self.settings)

    # -----------------
    # Start sensor
    # -----------------

    def begin(self):
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

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # EVENT PATTERN RECOGNITION
    #
    # In general these routines look at the sample_history buffer and
    # decide if an event has just become recognizable, e.g. POT_NEW
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Test if pot is EMPTY
    # True if median for 1 second is 1400 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def test_empty(self,offset):
        m, next_offset, duration, sample_count = self.sample_buffer.median(offset, 1)
        if not m == None:
            EMPTY_WEIGHT = 1400
            EMPTY_MARGIN = 100
            empty = abs(m - EMPTY_WEIGHT) < EMPTY_MARGIN
            confidence = 1 - abs(m - EMPTY_WEIGHT) / EMPTY_MARGIN / 2
            return (), next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if pot is FULL
    # True if median for 1 second is 3400 grams +/- 400
    # Returns tuple <Test true/false>, < next offset >
    def test_full(self,offset):
        m, next_offset, duration, sample_count = self.sample_buffer.median(offset, 1)
        if not m == None:
            FULL_WEIGHT = 3400
            FULL_MARGIN = 400
            full = abs(m - FULL_WEIGHT) < FULL_MARGIN
            confidence = 1 - abs(m - FULL_WEIGHT) / FULL_MARGIN / 2
            return full, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if pot is REMOVED
    # True if median for 3 seconds is 0 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def test_removed(self,offset):
        m, next_offset, duration, sample_count = self.sample_buffer.median(offset, 3)
        if not m == None:
            removed = abs(m) < 100
            confidence = 1 - abs(m) / 200
            return removed, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if cup has been POURED
    def test_event_poured(self, ts):

        now = self.sample_buffer.get(0)["ts"]

        # get latest 1-second median and deviation
        current_median, offset, duration, sample_count = self.sample_buffer.median(0,1)

        current_deviation, offset, duration, sample_count = self.sample_buffer.deviation(0,1,current_median)

        # COFFEE_POURED == False if current 1 second weight not stable
        if ( current_median is None or
             offset is None or
             duration is None or
             sample_count is None or
             current_deviation is None ):
            #print("{} no stats now".format(now))
            return None

        if current_deviation > 30:
            #print("{} deviation not stable = {}".format(now, current_deviation))
            return None

        #print("{} deviation ok = {}".format(now, current_deviation))

        push_detected = False

        # look back 15 seconds and see if push detected AND stable prior value was 100.500g higher than latest stable value
        POUR_TEST_SECONDS = 15
        for i in range(POUR_TEST_SECONDS):
            stats_record = self.stats_buffer.get(i)
            if stats_record is None:
                continue

            stats = stats_record["value"]

            # skip if we have no stats for current period
            if ( stats is None or
                 stats["median"] is None or
                 stats["deviation"] is None or
                 stats["duration"] is None or
                 stats["duration"] < 0.5 or
                 stats["sample_count"] is None or
                 stats["sample_count"] < 5 ):
                continue

            # check for push
            if not push_detected and stats["median"] >  current_median + 2000:
                push_detected = True
                #print("{} push detected at {}".format(now, stats_record["ts"]))
                continue

            # check for higher level of coffee before push
            med_delta = stats["median"] - current_median

            if push_detected and stats["deviation"] < 30 and med_delta > 100 and med_delta < 500:
                latest_event = self.event_buffer.get(0)
                if ((latest_event is None) or
                   (latest_event["value"]["event_code"] != EVENT_POURED) or
                   (ts - latest_event["ts"] > 30 )):
                    weight_poured = math.floor(med_delta + 0.5)
                    weight = math.floor(current_median + 0.5)
                    confidence = 0.8 # we don't have much better yet
                    return { "event_code": EVENT_POURED,
                             "weight_poured": weight_poured,
                             "weight": weight,
                             "acp_confidence": confidence
                           }
                #print(stats)
                #print("{} EVENT POURED amount={:.1f} from {}".format(now, med_delta, stats_record["ts"]))

        return None

    def test_event_new(self, ts):
        # Is the pot full now ?
        full, offset, full_weight, full_confidence = self.test_full(0)

        # Was it removed before ?
        removed, new_offset, removed_weight, removed_confidence = self.test_removed(offset)

        if removed and full:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != EVENT_NEW) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(full_weight+0.5)
                confidence = full_confidence * 0.7 + removed_confidence * 0.3
                return { "event_code": EVENT_NEW, "weight": weight, "acp_confidence": confidence }

        return None

    def test_event_removed(self, ts):
        # Is the pot removed now ?
        removed_now, offset, removed_now_weight, removed_now_confidence = self.test_removed(0)

        # Was it removed before ?
        removed_before, new_offset, removed_before_weight, removed_before_confidence = self.test_removed(offset)

        if removed_now and not removed_before:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != EVENT_REMOVED) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(removed_now_weight+0.5)
                confidence = removed_now_confidence
                return { "event_code": EVENT_REMOVED, "weight": weight, "acp_confidence": confidence }

        return None

    def test_event_empty(self, ts):
        # Is the pot empty now ?
        empty_now, offset, empty_weight, empty_confidence = self.test_empty(0)

        # Was it empty before ?
        empty_before, new_offset, empty_before_weight, empty_before_confidence = self.test_empty(offset)

        if empty_now and not empty_before:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != EVENT_EMPTY) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(empty_weight+0.5)
                confidence = empty_confidence
                return { "event_code": EVENT_REMOVED, "weight": weight, "acp_confidence": confidence }

        return None


    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    def test_event(self, ts, weight_g):
        for test in [ self.test_event_new,
                      self.test_event_removed,
                      self.test_event_poured,
                      self.test_event_empty
                    ]:
            event = test(ts)
            if not event is None:
                self.event_buffer.put(ts, event)
                self.send_event(ts, event)
                break

        return event

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

        #----------------
        # UPDATE DISPLAY
        # ---------------

        self.display.update(ts, self.sample_buffer, debug_list)

        # ----------------------
        # SEND EVENT TO PLATFORM
        # ----------------------

        self.test_event(ts, value)

        # ---------------------
        # SEND DATA TO PLATFORM
        # ---------------------

        if self.prev_send_time is None:
            self.prev_send_time = ts

        if ts - self.prev_send_time > 30:
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

