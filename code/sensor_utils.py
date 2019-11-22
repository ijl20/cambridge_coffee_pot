# Various utility functions

import time
from statistics import median

CONFIG = { "LOG_LEVEL": 1}

# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
# list_to_string() function
# 'pretty formats' a list for printing, i.e. '[ <value>, <value>, ...]'
# The actual values can be formatted with a format string, default '{}'
# e.g. '{:.3f}' will format number as a float with 3 decimal places.
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------

# Convert [1,2,3] to "1, 2, 3" using optional format string e.g "{:.1f}"
def list_to_string(input_list, format_string="{}"):
    output_string = ""

    first_separator = ""

    separator = ", " ## added *before* each element except first

    first_added = False # flag to detect whether we are currently adding first element

    for element in input_list:
        if not first_added:
            output_string = output_string + first_separator
            first_added = True
        else:
            output_string = output_string + separator

        # add the formatted element
        output_string = output_string + format_string.format(element)

    return output_string

# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------
#
# TimeBuffer class
#
# Implements a circular buffer of { "ts": , "value": } objects (where "ts" is the unix timestamp)
# Generally will return 'None' if method call cannot return a reasonable value (e.g. index in buffer
# is off the end of the buffer).
#
# Initialize with e.g. 'b = TimeBuffer(100)' where 100 is desired size of buffer.
#
# b.record_sample(value): add {"ts": <now>, "value": value } to buffer
#
# b.lookup_sample(offset): lookup entry at buffer index offset from now (now = offset ZERO).
#
# b.load_readings_file(filename): will reset buffer and load ts,value data from CSV file.
#
# b.average_time(time_offset, duration): find average value for
#   'duration' seconds ending time_offset seconds before latest reading
#
# b.median_time(time_offset, duration): as average_time, but return median value
#
# ---------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------

class TimeBuffer(object):

    def __init__(self, size=1000):
        print("TimeBuffer init size={}".format(size))

        # Note sample_history is a *circular* buffer (for efficiency)
        self.SAMPLE_HISTORY_SIZE = size # store value samples 0..(size-1)
        self.sample_history_index = 0
        self.sample_history = [ None ] * self.SAMPLE_HISTORY_SIZE # buffer for 100 value samples ~= 10 seconds

    # sample_history: global circular buffer containing { ts:, value:} datapoints
    # sample_history_index: global giving INDEX into buffer for NEXT datapoint

    # store the current value in the sample_history circular buffer
    def record_sample(self, value_g):
        self.sample_history[self.sample_history_index] = { 'ts': time.time(), 'value': value_g }
        if CONFIG["LOG_LEVEL"] == 1:
            print("record sample_history[{}]:\n{},{}".format(self.sample_history_index,
                                                        self.sample_history[self.sample_history_index]["ts"],
                                                        self.sample_history[self.sample_history_index]["value"]))

        self.sample_history_index = (self.sample_history_index + 1) % self.SAMPLE_HISTORY_SIZE

    # load timestamp,reading values from a CSV file
    def load(self, filename):
        global CONFIG
        if CONFIG["LOG_LEVEL"] == 1:
            print("loading readings file {}".format(filename))

        self.sample_history_index = 0
        self.sample_history = [ None ] * self.SAMPLE_HISTORY_SIZE # buffer for 100 value samples ~= 10 seconds

        try:
            with open(filename, "r") as fp:
                # read line from file
                line = fp.readline()
                while line:
                    line_values = line.split(',')
                    # skip lines (e.g. blank lines) that don't seem to have readings
                    if len(line_values) == 2:
                        ts = float(line_values[0])
                        value = float(line_values[1])
                        self.sample_history[self.sample_history_index] = { "ts": ts,
                                                                        "value": value }
                        print("{: >5} {:10.3f} {: >8}".format(self.sample_history_index,ts,value))
                        self.sample_history_index = (self.sample_history_index + 1) % self.SAMPLE_HISTORY_SIZE
                    line = fp.readline()

        except Exception as e:
            print("READINGS FILE ERROR. Can't read supplied filename {}".format(filename))
            print(e)

    # Lookup the value in the sample_history buffer at offset before now (offset ZERO = latest value)
    # This returns None or an object { 'ts': <timestamp>, 'value': <grams> }
    def lookup_sample(self, offset):
        if offset >= self.SAMPLE_HISTORY_SIZE:
            if CONFIG["LOG_LEVEL"] == 1:
                print("lookup_sample offset too large, returning None")
            return None
        index = (self.sample_history_index + self.SAMPLE_HISTORY_SIZE - offset - 1) % self.SAMPLE_HISTORY_SIZE
        if CONFIG["LOG_LEVEL"] == 1:
            if self.sample_history[index] is not None:
                debug_str = "lookup_sample current {}, offset {} => {}: {:.2f} {:.1f}"
                print(debug_str.format( self.sample_history_index,
                                        offset,
                                        index,
                                        self.sample_history[index]["ts"],
                                        self.sample_history[index]["value"]))
            else:
                debug_str = "lookup_sample None @ current {}, offset {} => {}"
                print(debug_str.format( self.sample_history_index,
                                        offset,
                                        index))
        return self.sample_history[index]

    # Iterate backwards through sample_history buffer to find index of reading at a given time offset
    def time_to_offset(self,time_offset):
        if CONFIG["LOG_LEVEL"] == 1:
            print("time_to_offset",time_offset)

        sample = self.lookup_sample(0)
        if sample == None:
            return None

        sample_time = sample["ts"]

        time_limit = sample["ts"] - time_offset

        offset = 0

        while sample_time > time_limit:
            offset += 1
            if offset >= self.SAMPLE_HISTORY_SIZE:
                print("time_to_offset ({}) exceeded buffer size")
                return None
            sample = self.lookup_sample(offset)
            if sample == None:
                return None
            sample_time = sample["ts"]

        return offset

    # Calculate the average value recorded over the previous 'duration' seconds from time_offset seconds.
    # Returns a tuple of <average value>, <index> where <index> is the sample_history offset
    # one sample earlier than the offset & duration selected.
    # E.g. average_time(0,3) will find the average value of the most recent 3 seconds.
    # average_time(2,1) will find average during 1 second duration ending 2 seconds ago.
    def average_time(self, time_offset, duration):
        if CONFIG["LOG_LEVEL"] == 1:
            print("average_time time_offset={}, duration={}".format(time_offset, duration))

        offset = self.time_to_offset(time_offset)

        # lookup the first value to get that value (grams) and timestamp
        sample = self.lookup_sample(offset)
        if sample == None:
            return None, offset

        next_offset = offset
        total_value = sample["value"]
        begin_limit = sample["ts"] - duration
        sample_count = 1
        while True: # Repeat .. Until
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                # we've exhausted the full buffer
                return None
            sample = self.lookup_sample(next_offset)
            if sample == None:
                # we've exhausted the values in the partially filled buffer
                return None
            if sample["ts"] < begin_limit:
                break
            total_value += sample["value"]
            sample_count += 1

        if CONFIG["LOG_LEVEL"] == 1:
            print("average_time total {} average {} with {} samples".format(total_value,
                                                                            total_value/sample_count,
                                                                            sample_count))
        return total_value / sample_count, next_offset

    # Return the median sample value for a time period.
    # The period is from (latest sample time - time_offset) to (latest sample time - time_offset - duration)
    # All time values are in seconds.
    # Returns a tuple of <median sensor reading>, <index> where <index> is the sample_history offset
    def median_time(self, time_offset, duration):

        if CONFIG["LOG_LEVEL"] == 1:
            print("median_time time_offset={}, duration={}".format(time_offset, duration))

        # Convert time (e.g. 3 seconds) to an index offset from latest reading in sample_history
        offset = self.time_to_offset(time_offset)

        sample = self.lookup_sample(offset)
        if sample == None:
            return None, offset
        next_offset = offset

        begin_limit = sample["ts"] - duration
        if CONFIG["LOG_LEVEL"] == 1:
            print("median_time begin_limit={}".format(begin_limit))

        begin_time = sample["ts"] # this will be updated as we loop, to find duration available
        end_time = sample["ts"]

        #if CONFIG["LOG_LEVEL"] == 1:
        #    print("median_time begin_time {:.3f}".format(begin_time))

        value_list = [ sample["value"] ]
        while True: # Repeat .. Until
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                # we've exhausted the full buffer
                break

            sample = self.lookup_sample(next_offset)

            if sample == None:
                print("median_time looked back to None value")
                # we've exhausted the values in the partially filled buffer
                break

            # see if we have reached the end of the intended period
            if sample["ts"] < begin_limit:
                break

            value_list.append(sample["value"])

            begin_time = sample["ts"]

        # If we didn't get enough samples, return with error
        if len(value_list) < 3:
            print("median_time not enough samples ({})".format(len(value_list)))
            return None, None

        # Now we have a list of samples with the required duration
        median_value = median(value_list)

        if CONFIG["LOG_LEVEL"] == 1:
            print("value_median for {:.3f} seconds with {} samples = {}".format(end_time - begin_time,
                                                                                len(value_list),
                                                                                median_value))

        return median_value, next_offset
