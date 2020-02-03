
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# EVENT PATTERN RECOGNITION
#
# Instantiate with e = Events(settings)

# Provides a ".test(ts,sensor_id)" method which returns a (typically empty)
# list of events.
# Each event is a python dictionary, e.g.
# { "event_code": EventCode.EMPTY, "weight": weight, "acp_confidence": confidence }
#
# In general these routines look at the TimeBuffers and
# decide if an event has just become recognizable, e.g. COFFEE_NEW
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import math

from classes.time_buffer import TimeBuffer

# COFFEE POT CONSTANTS
class EventCode(object):
    STARTUP = "COFFEE_STARTUP"
    NEW = "COFFEE_NEW"
    EMPTY = "COFFEE_EMPTY"
    POURED = "COFFEE_POURED"
    REMOVED = "COFFEE_REMOVED"
    REPLACED = "COFFEE_REPLACED"
    GRINDING = "COFFEE_GRINDING"
    BREWING = "COFFEE_BREWING"

    # Periodic 'watchdog' events
    STATUS = "COFFEE_STATUS"
    GRIND_STATUS = "GRIND_STATUS"
    BREW_STATUS = "BREW_STATUS"

    INFO = { "COFFEE_STARTUP": { "text": "STARTUP" },
             "COFFEE_NEW": { "text": "NEW", "value": "weight_new" },
             "COFFEE_EMPTY": { "text": "EMPTY" },
             "COFFEE_POURED": { "text": "POUR", "value": "weight_poured" },
             "COFFEE_REMOVED": { "text": "REMOVED" },
             "COFFEE_REPLACED": { "text": "REPLACED" },
             "COFFEE_GRINDING": { "text": "GRINDING" },
             "COFFEE_BREWING": { "text": "BREWING" }
           }

class Events(object):

    def __init__(self, settings=None):

        # set up the various timebuffers
        self.settings = settings


        # CONSTS
        self.EMPTY_WEIGHT = 1630
        self.EMPTY_MARGIN = 50
        self.FULL_WEIGHT = 3400
        self.FULL_MARGIN = 400
        self.REMOVED_WEIGHT = 0
        self.REMOVED_MARGIN = 100

        # Create event buffer for sensor node, i.e. common to all sensors
        self.event_buffer = TimeBuffer(size=1000, settings=self.settings)

        # Create dictionary to reference buffers for each sensor
        # This Events object will be passed to each sensor __init__ so the sensor will add its buffers to sensor_buffers.
        self.sensor_buffers = {}

    # Test if value represents EMPTY pot
    def empty_value(self, x):
        if x==None:
            return False, 1
        empty = abs(x - self.EMPTY_WEIGHT) < self.EMPTY_MARGIN
        confidence = 1 - abs(x - self.EMPTY_WEIGHT) / self.EMPTY_MARGIN / 2
        return empty, confidence

    # Test if value represents a FULL pot
    def full_value(self, x):
        if x==None:
            return False, 1
        full = abs(x - self.FULL_WEIGHT) < self.FULL_MARGIN
        confidence = 1 - abs(x - self.FULL_WEIGHT) / self.FULL_MARGIN / 2
        return full, confidence

    # Test if value represents the pot REMOVED
    def removed_value(self, x):
        #print("removed_value()",x)
        if x==None:
            return False, 1
        removed = abs(x - self.REMOVED_WEIGHT) < self.REMOVED_MARGIN
        confidence = 1 - abs(x-self.REMOVED_WEIGHT) / (2 * self.REMOVED_MARGIN)
        #print("removed_value()",x,removed)
        return removed, confidence

    # Test if pot is EMPTY
    # True if median for 1 second is 1400 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def is_empty(self,offset):
        sample_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]
        m, next_offset, duration, sample_count = sample_buffer.median(offset, 1)
        d, next_offset, duration, sample_count = sample_buffer.deviation(offset, 1, m)
        if (not m is None and
            not sample_count is None and
            sample_count > 5 and
            not d is None and
            not d > 30):

            empty, confidence = self.empty_value(m)

            return empty, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if pot is FULL
    # True if median for 1 second is 3400 grams +/- 400
    # Returns tuple <Test true/false>, < next offset >
    def is_full(self,offset):
        sample_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]
        m, next_offset, duration, sample_count = sample_buffer.median(offset, 1)
        d, next_offset, duration, sample_count = sample_buffer.deviation(offset, 1, m)
        if (not m is None and
            not sample_count is None and
            sample_count > 5 and
            not d is None and
            not d > 30):

            full, confidence = self.full_value(m)

            return full, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if pot is REMOVED
    # True if median for 3 seconds is 0 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def is_removed(self,offset):
        sample_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]
        m, next_offset, duration, sample_count = sample_buffer.median(offset, 3)
        if not m == None:

            removed, confidence = self.removed_value(m)

            return removed, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if cup has been POURED
    def test_event_poured(self, ts):
        sample_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]

        now = sample_buffer.get(0)["ts"]

        # get latest 1-second median and deviation
        current_median, offset, duration, sample_count = sample_buffer.median(0,1)

        current_deviation, offset, duration, sample_count = sample_buffer.deviation(0,1,current_median)

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

        # look back and see if push detected AND stable prior value was higher than latest stable value
        POUR_TEST_SECONDS = 30
        # We are using the fact that each index in stats_buffer represents ONE SECOND of readings
        for i in range(POUR_TEST_SECONDS):
            stats_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["stats_buffer"]
            stats_record = stats_buffer.get(i)
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

            MIN_CUP_WEIGHT = 40
            MAX_CUP_WEIGHT = 1000
            if ( push_detected and
                 stats["deviation"] < 30 and
                 med_delta > MIN_CUP_WEIGHT and
                 med_delta < MAX_CUP_WEIGHT):

                #latest_event = self.event_buffer.get(0)
                #if ((latest_event is None) or
                #   (latest_event["value"]["event_code"] != EventCode.POURED) or
                #   (ts - latest_event["ts"] > 30 )):

                weight_poured = math.floor(med_delta + 0.5)
                weight = math.floor(current_median + 0.5)

                is_poured_event = lambda event_sample: event_sample['value']['event_code'] == EventCode.POURED

                prev_poured, offset, duration, count = self.event_buffer.find(0,POUR_TEST_SECONDS,is_poured_event)

                # Only send this POURED event if there isn't already a recent POURED event with similar weight
                if prev_poured is None or prev_poured['value']['weight'] - weight > MIN_CUP_WEIGHT:
                    confidence = 0.8 # we don't have much better yet
                    return { "event_code": EventCode.POURED,
                             "weight_poured": weight_poured,
                             "weight": weight,
                             "acp_confidence": confidence
                           }
                #print(stats)
                #print("{} EVENT POURED amount={:.1f} from {}".format(now, med_delta, stats_record["ts"]))

        return None

    def test_event_new(self, ts):
        REMOVED_TEST_SECONDS = 30 # pot must previously have been removed for at least this long
        PREVIOUS_NEW_TEST_SECONDS = 60 # there must not have been a NEW event within this time
        # Is the pot full now ?
        full, offset, full_weight, full_confidence = self.is_full(0)

        # Immediate return if pot not full now
        if not full:
            return None

        if self.settings["LOG_LEVEL"] <= 1:
            print("{:.3f} test_event_new is_full".format(ts))

        # Was pot REMOVED during previous 30 seconds ?
        # define stats_buffer sample test function
        removed_test = lambda stats_sample: self.removed_value(stats_sample['value']['median'])[0]

        # look in stats_buffer to try and find 'removed' 1-second median
        stats_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["stats_buffer"]
        stats_removed, stats_offset, stats_duration, stats_count = stats_buffer.find(0, REMOVED_TEST_SECONDS, removed_test)

        if stats_removed != None:
            if self.settings["LOG_LEVEL"] <= 1:
                print("{:.3f} test_event_new stats_removed test succeeded".format(ts))

            # ok we found a previous 'removed' median

            is_new_event = lambda event_sample: event_sample['value']['event_code'] == EventCode.NEW

            previous_new_event, offset, duration, count = self.event_buffer.find(0, PREVIOUS_NEW_TEST_SECONDS, is_new_event )

            if previous_new_event is None:
                # and we have no previous NEW event
                weight = math.floor(full_weight+0.5)
                confidence = full_confidence
                return { "event_code": EventCode.NEW,
                         "weight": weight,
                         "weight_new": weight - self.settings["WEIGHT_EMPTY"],
                         "acp_confidence": confidence }
            else:
                if self.settings["LOG_LEVEL"] <= 1:
                    print("{:.3f} NEW suppressed due to prior NEW".format(ts))

        elif self.settings["LOG_LEVEL"] <= 1:
            print("{:.3f} remove_test failed".format(ts))

        return None

    def test_event_removed(self, ts):
        # Is the pot removed now ?
        removed_now, offset, removed_now_weight, removed_now_confidence = self.is_removed(0)

        # Immediate exit if pot does not seem 'removed' now
        if not removed_now:
            return None

        # Was it removed before ?
        removed_before, new_offset, removed_before_weight, removed_before_confidence = self.is_removed(offset)

        if not removed_before:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != EventCode.REMOVED) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(removed_now_weight+0.5)
                confidence = removed_now_confidence
                return { "event_code": EventCode.REMOVED, "weight": weight, "acp_confidence": confidence }

        return None

    def test_event_replaced(self, ts):
        sample_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["sample_buffer"]

        # fast fail if latest weight reading < EMPTY_WEIGHT
        latest_sample = sample_buffer.get(0)

        if latest_sample is None or latest_sample["value"] < self.EMPTY_WEIGHT * 0.9: # 10% error margin
            return None

        now = sample_buffer.get(0)["ts"]

        # get latest 1-second median and deviation
        current_median, offset, duration, sample_count = sample_buffer.median(0,1)

        #print("test_event_replaced() median {:.1f}".format(current_median))

        current_deviation, offset, duration, sample_count = sample_buffer.deviation(0,1,current_median)

        # COFFEE_POURED == False if current 1 second weight not stable
        if ( current_median is None or
             offset is None or
             duration is None or
             sample_count is None or
             current_deviation is None ):
            #print("{} no stats now".format(now))
            return None

        if current_median < self.EMPTY_WEIGHT * 0.9:
            #print("test_event_replaced() median too small for replaced")
            return None

        if current_deviation > 30:
            #print("test_event_replaced() deviation not stable = {}".format(current_deviation))
            return None

        # Was pot REMOVED during previous 3 seconds ?
        # define stats_buffer sample test function
        removed_test = lambda stats_sample: self.removed_value(stats_sample['value']['median'])[0]

        # look in stats_buffer to try and find 'removed' 1-second median
        stats_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["stats_buffer"]

        stats_removed, stats_offset, stats_duration, stats_count = stats_buffer.find(0, 3, removed_test)

        if stats_removed != None:
            if self.settings["LOG_LEVEL"] <= 1:
                print("{:.3f} test_event_replaced() stats_removed test succeeded".format(ts))

            # ok we found a previous 'removed' median

            is_replaced_event = lambda event_sample: event_sample['value']['event_code'] == EventCode.REPLACED

            previous_event, offset, duration, count = self.event_buffer.find(0, 3, is_replaced_event )

            if previous_event is None:
                # we have no previous REPLACED event in past 3 seconds
                weight = math.floor(current_median+0.5)
                confidence = 0.8 #debug need to calculate a reasonable figure
                return { "event_code": EventCode.REPLACED, "weight": weight, "acp_confidence": confidence }
            elif self.settings["LOG_LEVEL"] <= 1:
                print("{:.3f} REPLACED suppressed due to prior event".format(ts))

        elif self.settings["LOG_LEVEL"] <= 1:
            print("{:.3f} test_event_replaced() remove_test failed".format(ts))

        return None

    def test_event_empty(self, ts):
        # Is the pot empty now ?
        empty_now, offset, empty_weight, empty_confidence = self.is_empty(0)

        # Immediate return if pot doesn't seem empty now
        if not empty_now:
            return None

        # Was pot NOT EMPTY during previous 30 seconds ?
        EMPTY_TEST_SECONDS = 30
        # define stats_buffer sample test function
        not_empty = lambda stats_sample: not self.empty_value(stats_sample['value']['median'])[0]
        # look in stats_buffer to try and find 'not empty' 1-second median
        stats_buffer = self.sensor_buffers[self.settings["WEIGHT_SENSOR_ID"]]["stats_buffer"]
        stats_not_empty, stats_offset, stats_duration, stats_count = stats_buffer.find(0, EMPTY_TEST_SECONDS, not_empty)

        #print(ts,"test_event_empty: empty_now, stats_not_empty=", stats_not_empty)

        if stats_not_empty != None:
            #latest_event = self.event_buffer.get(0)
            #if ((latest_event is None) or
            #   (latest_event["value"]["event_code"] != EventCode.EMPTY) or
            #   (ts - latest_event["ts"] > 600 )):
            PREVIOUS_EMPTY_TEST_SECONDS = 60

            is_empty_event = lambda event_sample: event_sample['value']['event_code'] == EventCode.EMPTY

            previous_empty_event, offset, duration, count = self.event_buffer.find(0, PREVIOUS_EMPTY_TEST_SECONDS, is_empty_event )

            if previous_empty_event is None:
                weight = math.floor(empty_weight+0.5)
                confidence = empty_confidence

                #print(ts, "test_event_empty: returning EMPTY")
                return { "event_code": EventCode.EMPTY, "weight": weight, "acp_confidence": confidence }
            #else:
                #print(ts,"test_event_empty: returning None due to previous EMPTY at ",previous_empty_event['ts'])

        return None

    # Test any event after a GRIND reading
    def test_grind(self, ts):
        GRIND_POWER = 9 #debug - power (watts) threshold for valid 'GRINDING'
        # TimeBuffer.get() returns {"ts": , "value": }
        sample = self.sensor_buffers[self.settings["GRIND_SENSOR_ID"]]["sample_buffer"].get(0)

        value = sample["value"]

        # debug - maybe we can create a more meaningful confidence value
        confidence = 0.81

        if "ENERGY" in value and "Power" in value["ENERGY"]:
            power = value["ENERGY"]["Power"]
            if power > GRIND_POWER:
                return { "event_code": EventCode.GRINDING,
                         "power": power,
                         "value": value,
                         "acp_confidence": confidence }

        return { "event_code": EventCode.GRIND_STATUS, "value": value, "acp_confidence": confidence }

    # Test any event after a BREW reading
    def test_brew(self, ts):
        BREW_POWER = 9 #debug - power (watts) threshold for valid 'BREWING'
        # get latest sample from BREW sample buffer
        sample = self.sensor_buffers[self.settings["BREW_SENSOR_ID"]]["sample_buffer"].get(0)

        value = sample["value"]

        # debug - maybe we can create a more meaningful confidence value
        confidence = 0.82

        if "ENERGY" in value and "Power" in value["ENERGY"]:
            power = value["ENERGY"]["Power"]
            if power > BREW_POWER:
                return { "event_code": EventCode.BREWING,
                         "power": power,
                         "value": value,
                         "acp_confidence": confidence }

        return { "event_code": EventCode.BREW_STATUS, "value": value, "acp_confidence": confidence }

    def test(self, ts, sensor_id):

        if sensor_id == self.settings["WEIGHT_SENSOR_ID"]:
            tests = [ self.test_event_new,
                      self.test_event_removed,
                      self.test_event_poured,
                      self.test_event_empty,
                      self.test_event_replaced
                    ]

        elif sensor_id == self.settings["GRIND_SENSOR_ID"]:
            tests = [ self.test_grind ]

        elif sensor_id == self.settings["BREW_SENSOR_ID"]:
            tests = [ self.test_brew ]

        else:
            raise NameError("Bad sensor id: {}".format(sensor_id))

        event_list = []
        for test_function in tests:
            event = test_function(ts)
            if not event is None:
                event_list.append(event)
                self.event_buffer.put(ts,event)

        return event_list

