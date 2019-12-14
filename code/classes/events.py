
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# EVENT PATTERN RECOGNITION
#
# In general these routines look at the sample_history buffer and
# decide if an event has just become recognizable, e.g. POT_NEW
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import math

class Events(object):

    def __init__(self, 
                 settings=None,
                 sample_buffer=None,
                 event_buffer=None,
                 stats_buffer=None
                ):
        # COFFEE POT EVENTS

        self.EVENT_NEW = "COFFEE_NEW"
        self.EVENT_EMPTY = "COFFEE_EMPTY"
        self.EVENT_POURED = "COFFEE_POURED"
        self.EVENT_REMOVED = "COFFEE_REMOVED"
        self.EVENT_GROUND = "COFFEE_GROUND"

        self.settings = settings
        self.sample_buffer = sample_buffer
        self.event_buffer = event_buffer
        self.stats_buffer = stats_buffer

    # Test if pot is EMPTY
    # True if median for 1 second is 1400 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def test_empty(self,offset):
        m, next_offset, duration, sample_count = self.sample_buffer.median(offset, 1)
        d, next_offset, duration, sample_count = self.sample_buffer.deviation(offset, 1, m)
        if (not m is None and
            not sample_count is None and
            sample_count > 5 and
            not d is None and
            not d > 30):

            EMPTY_WEIGHT = 1600
            EMPTY_MARGIN = 100
            empty = abs(m - EMPTY_WEIGHT) < EMPTY_MARGIN
            confidence = 1 - abs(m - EMPTY_WEIGHT) / EMPTY_MARGIN / 2
            return empty, next_offset, m, confidence
        else:
            return None, None, None, None

    # Test if pot is FULL
    # True if median for 1 second is 3400 grams +/- 400
    # Returns tuple <Test true/false>, < next offset >
    def test_full(self,offset):
        m, next_offset, duration, sample_count = self.sample_buffer.median(offset, 1)
        d, next_offset, duration, sample_count = self.sample_buffer.deviation(offset, 1, m)
        if (not m is None and
            not sample_count is None and
            sample_count > 5 and
            not d is None and
            not d > 30):

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
        POUR_TEST_SECONDS = 30
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

            MIN_CUP_WEIGHT = 40
            MAX_CUP_WEIGHT = 1000
            if push_detected and stats["deviation"] < 30 and med_delta > MIN_CUP_WEIGHT and med_delta < MAX_CUP_WEIGHT:
                latest_event = self.event_buffer.get(0)
                if ((latest_event is None) or
                   (latest_event["value"]["event_code"] != self.EVENT_POURED) or
                   (ts - latest_event["ts"] > 30 )):
                    weight_poured = math.floor(med_delta + 0.5)
                    weight = math.floor(current_median + 0.5)
                    confidence = 0.8 # we don't have much better yet
                    return { "event_code": self.EVENT_POURED,
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
               (latest_event["value"]["event_code"] != self.EVENT_NEW) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(full_weight+0.5)
                confidence = full_confidence * 0.7 + removed_confidence * 0.3
                return { "event_code": self.EVENT_NEW, "weight": weight, "acp_confidence": confidence }

        return None

    def test_event_removed(self, ts):
        # Is the pot removed now ?
        removed_now, offset, removed_now_weight, removed_now_confidence = self.test_removed(0)

        # Was it removed before ?
        removed_before, new_offset, removed_before_weight, removed_before_confidence = self.test_removed(offset)

        if removed_now and not removed_before:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != self.EVENT_REMOVED) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(removed_now_weight+0.5)
                confidence = removed_now_confidence
                return { "event_code": self.EVENT_REMOVED, "weight": weight, "acp_confidence": confidence }

        return None

    def test_event_empty(self, ts):
        # Is the pot empty now ?
        empty_now, offset, empty_weight, empty_confidence = self.test_empty(0)

        # Was it empty before ?
        empty_before, new_offset, empty_before_weight, empty_before_confidence = self.test_empty(offset)

        if empty_now and not empty_before:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"]["event_code"] != self.EVENT_EMPTY) or
               (ts - latest_event["ts"] > 600 )):
                weight = math.floor(empty_weight+0.5)
                confidence = empty_confidence
                return { "event_code": self.EVENT_EMPTY, "weight": weight, "acp_confidence": confidence }

        return None


    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    def test(self, ts, weight_g):
        events = []
        for test_function in [ self.test_event_new,
                               self.test_event_removed,
                               self.test_event_poured,
                               self.test_event_empty
                    ]:
            event = test_function(ts)
            if not event is None:
                events.append(event)

        return events


