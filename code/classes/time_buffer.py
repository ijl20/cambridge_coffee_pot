
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
# b.put(ts, value): add {"ts": ts, "value": value } to buffer
#
# b.get(offset): lookup entry at buffer index offset from now (now = offset ZERO).
#
# b.mean(offset, duration): find mean value for
#   'duration' seconds ending at the buffer index 'offset' before latest reading
#
# b.median(offset, duration): as mean(), but return median value
#
# b.time_to_offset(offset, duration): given a duration in seconds, return the index of the
#       first buffer sample that is earlier or equal to that time offset from the
#       sample at buffer.get(offset)
#
# File handling utility methods:
#
#   b.load(filename): will reset buffer and load ts,value data from CSV file.
#
#   b.save(filename): will store contents of buffer to ts,value CSV file
#
#   b.play(callback, realtime, sleep): 'replay' data from the buffer, calling 'callback(ts,value)' for each
#       sample in the buffer. If 'realtime' is True (default False) then play will sleep for the original
#       delta of time before calling the callback, otherwise if 'sleep' is non-zero (default=0.0) then
#       play will sleep for that number of seconds before calling the callback.
#
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------

import time
from statistics import median

DEFAULT_SETTINGS = { "LOG_LEVEL": 3 } # we need to pass this in the instantiation...

class TimeBuffer(object):

    def __init__(self, size=1000, settings=None, stats_buffer=None):
        print("TimeBuffer init size={}".format(size))

        if settings is None:
            self.settings = DEFAULT_SETTINGS
        else:
            self.settings = settings

        self.stats_buffer = stats_buffer

        self.size = size

        # keep track of how many samples are in buffer (max = self.size)
        self.samples = 0

        # Note sample_history is a *circular* buffer (for efficiency)
        self.SAMPLE_HISTORY_SIZE = size # store value samples 0..(size-1)
        self.sample_history_index = 0
        self.sample_history = [ None ] * self.SAMPLE_HISTORY_SIZE # buffer for 100 value samples ~= 10 seconds

    # sample_history: global circular buffer containing { ts:, value:} datapoints
    # sample_history_index: global giving INDEX into buffer for NEXT datapoint

    # store the current value in the sample_history circular buffer
    def put(self, ts, value):
        self.sample_history[self.sample_history_index] = { 'ts': ts, 'value': value }
        if self.settings["LOG_LEVEL"] == 1:
            print("record sample_history[{}]:\n{},{}".format(self.sample_history_index,
                                                        self.sample_history[self.sample_history_index]["ts"],
                                                        self.sample_history[self.sample_history_index]["value"]))

        self.sample_history_index = (self.sample_history_index + 1) % self.SAMPLE_HISTORY_SIZE

        # Increment the samples count
        if self.samples < self.size:
            self.samples += 1

        # If a StatsBuffer is associated with this TimeBuffer, update it
        if not self.stats_buffer is None:
            self.stats_buffer.update(self)

    # Lookup the value in the sample_history buffer at offset before now (offset ZERO = latest value)
    # This returns None or an object { 'ts': <timestamp>, 'value': <grams> }
    def get(self, offset=0):
        if offset == None:
            return None
        if offset >= self.SAMPLE_HISTORY_SIZE:
            if self.settings["LOG_LEVEL"] == 1:
                print("get offset too large, returning None")
            return None
        index = (self.sample_history_index + self.SAMPLE_HISTORY_SIZE - offset - 1) % self.SAMPLE_HISTORY_SIZE
        if self.settings["LOG_LEVEL"] == 1:
            if self.sample_history[index] is not None:
                debug_str = "get current {}, offset {} => {}: {:.2f} {}"
                print(debug_str.format( self.sample_history_index,
                                        offset,
                                        index,
                                        self.sample_history[index]["ts"],
                                        self.sample_history[index]["value"]))
            else:
                debug_str = "get None @ current {}, offset {} => {}"
                print(debug_str.format( self.sample_history_index,
                                        offset,
                                        index))
        return self.sample_history[index]

    # load timestamp,reading values from a CSV file
    def load(self, filename):
        if self.settings["LOG_LEVEL"] <= 2:
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
                        #self.sample_history[self.sample_history_index] = { "ts": ts,
                        #                                                "value": value }
                        self.put(ts,value)
                        if self.settings["LOG_LEVEL"] == 1:
                            print("{: >5} {:10.3f} {: >8}".format(self.sample_history_index,ts,value))
                        #self.sample_history_index = (self.sample_history_index + 1) % self.SAMPLE_HISTORY_SIZE
                    line = fp.readline()

        except Exception as e:
            print("LOAD FILE ERROR. Can't read supplied filename {}".format(filename))
            print(e)

    # Save the buffer contents to a file as <ts>,<value> CSV records, oldest to newest
    def save(self, filename):
        index = self.sample_history_index # index of oldest entry (could be None if buffer not wrapped)
        finish_index = self.sample_history_index
        finished = False
        try:
            if self.settings["LOG_LEVEL"] <= 3:
                print("Saving TimeBuffer to {}".format(filename))

            with open(filename,"w+") as fp:
                # we will loop through the buffer until at latest value at sample_history_index-1
                while not finished:
                    sample = self.sample_history[index]
                    # skip None samples
                    if sample != None:
                        sample_value = sample["value"]
                        # Add quotes for CSV if necessary
                        if isinstance(sample_value, str):
                            sample_value = '"'+sample_value+'"'
                        fp.write("{},{}\n".format(sample["ts"], sample_value))
                    index = (index + 1) % self.SAMPLE_HISTORY_SIZE
                    if index == finish_index:
                        finished = True

        except Exception as e:
            print("SAVE FILE ERROR {}".format(filename))
            print(e)

    # Pump all the <time, value> buffer samples through a provided processing function.
    # I.e. will call 'process_sample(ts, value)' for each sample in the buffer.
    def play(self, process_sample, realtime=False, sleep=0.0 ):
        if self.settings["LOG_LEVEL"] <= 2:
            print("TimeBuffer.play() from buffer index:", self.sample_history_index)
        index = self.sample_history_index # index of oldest entry (could be None if buffer not wrapped)
        finish_index = self.sample_history_index
        finished = False
        prev_ts = None # used to calculate realtime delay between playback of samples

        # we will loop through the buffer until at latest value at sample_history_index-1
        while not finished:

            if self.settings["LOG_LEVEL"] == 1:
                print("TimeBuffer play index", index)

            sample = self.sample_history[index]

            # process 'not None' samples
            if sample != None:
                # And sleep() if we want realistic animation
                # if realtime then sleep for period between samples
                if realtime:
                    if not prev_ts is None:
                        time.sleep(sample["ts"] - prev_ts)
                    prev_ts = sample["ts"]
                # of if sleep value is provided then sleep that long
                elif not sleep == 0:
                    time.sleep(sleep)
                # otherwise we will not sleep at all, and process the data without delay
                # HERE WE CALL THE PROVIDED FUNCTION
                process_sample(sample["ts"], sample["value"])

            index = (index + 1) % self.SAMPLE_HISTORY_SIZE
            if index == finish_index:
                finished = True

        if self.settings["LOG_LEVEL"] <= 2:
            print("TimeBuffer play finished")

    # Iterate backwards through sample_history buffer from offset to find index of earlier sample at least 'duration'
    # seconds earlier.
    def time_to_offset(self, offset=0, duration=0):
        if self.settings["LOG_LEVEL"] == 1:
            print("time_to_offset {} {}".format(offset,duration))

        sample = self.get(offset)
        if sample == None:
            return None

        sample_time = sample["ts"]

        time_limit = sample["ts"] - time_offset

        current_offset = offset

        while sample_time > time_limit:
            current_offset += 1
            if current_offset >= self.SAMPLE_HISTORY_SIZE:
                if self.settings["LOG_LEVEL"] <= 2:
                    print("time_to_offset ({}) exceeded buffer size".format(offset))
                return None
            sample = self.get(current_offset)
            if sample == None:
                return None
            sample_time = sample["ts"]

        return current_offset

    # Calculate the average value recorded over the previous 'duration' seconds from INDEX offset
    # Returns tuple (average_value, next_offset, actual_duration, sample_count)
    # Parameters:
    #       offset: buffer index offset (0=latest) for start of calculation
    #       duration: time period (seconds) over which to calculate return value
    # Return tuple:
    #       average_value = calculated mean
    #       next_offset = offset in buffer of 1st sample older than latest - duration
    #       actual_duration = time span of data samples used in calculation
    #       sample_count = how many buffer values were used when calculating mean value
    def mean(self, offset, duration):
        # lookup the first value to get that value (grams) and timestamp
        sample = self.get(offset)
        if sample == None:
            return None, None, None, None

        next_offset = offset
        total_value = sample["value"]
        begin_limit = sample["ts"] - duration
        sample_count = 1
        begin_time = sample["ts"]
        end_time = sample["ts"]

        while True: # Repeat .. Until
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                # we've exhausted the full buffer
                return None, None, None, None
            sample = self.get(next_offset)
            if sample == None:
                # we've exhausted the values in the partially filled buffer
                return None, None, None, None
            if sample["ts"] < begin_limit:
                break
            total_value += sample["value"]
            sample_count += 1
            begin_time = sample["ts"]

        if self.settings["LOG_LEVEL"] == 1:
            print("mean {} duration {} with {} samples".format( total_value/sample_count, end_time - begin_time, sample_count))
        return total_value / sample_count, next_offset, end_time - begin_time, sample_count

    # Return the median sample value for a time period.
    # Duration (the length of time to include samples) is still in seconds
    # Parameters:
    #       offset: buffer index offset (0=latest) for start of calculation
    #       duration: time period (seconds) over which to calculate return value
    # Return tuple:
    #       median_value = calculated median
    #       next_offset = offset in buffer of 1st sample older than latest - duration
    #       actual_duration = actual sample period used in median calculation
    #       sample_count = how many buffer values were used when calculating median value
    def median(self, offset, duration):

        sample = self.get(offset)
        if sample == None:
            return None, None, None, None

        next_offset = offset

        begin_limit = sample["ts"] - duration
        if self.settings["LOG_LEVEL"] == 1:
            print("median begin_limit={}".format(begin_limit))

        begin_time = sample["ts"] # this will be updated as we loop, to find duration available
        end_time = sample["ts"]

        #if self.settings["LOG_LEVEL"] == 1:
        #    print("median_time begin_time {:.3f}".format(begin_time))

        value_list = [ sample["value"] ]
        while True: # Repeat .. Until
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                # we've exhausted the full buffer
                break

            sample = self.get(next_offset)

            if sample == None:
                if self.settings["LOG_LEVEL"] == 1:
                    print("median looked back to None value")
                # we've exhausted the values in the partially filled buffer
                break

            # see if we have reached the end of the intended period
            if sample["ts"] < begin_limit:
                break

            value_list.append(sample["value"])

            begin_time = sample["ts"]

        # If we didn't get enough samples, return with error
        if len(value_list) < 3:
            if self.settings["LOG_LEVEL"] == 1:
                print("median not enough samples ({})".format(len(value_list)))
            return None, None, None, None

        # Now we have a list of samples with the required duration
        median_value = median(value_list)

        if self.settings["LOG_LEVEL"] == 1:
            print("median_value for {:.3f} seconds with {} samples = {}".format(end_time - begin_time,
                                                                                len(value_list),
                                                                                median_value))

        return median_value, next_offset, end_time - begin_time, len(value_list)

    # deviation() returns the deviation of a set of values around a provided value
    # Parameters:
    #       offset: index offset (latest sample = 0, previous = 1 etc)
    #       duration: time in seconds over which to find the standard deviation
    #       avg: average about which to calculate the deviation
    # Returns tuple (deviation_value, next_offset, actual_duration, sample_count)
    # where deviation_value = calculated deviation
    #       next_offset = offset in buffer of 1st sample older than latest - duration.
    #       actual_duration = duration (seconds) from oldest to newest in deviation calculation.
    #       sample_count = how many buffer values were used when calculating deviation value.
    def deviation(self, offset, duration, avg):
        if avg is None:
            return None, None, None, None

        # lookup the first value to get that value (grams) and timestamp
        sample = self.get(offset)
        if sample is None:
            return None, None, None, None

        next_offset = offset
        total_variance = (sample["value"] - avg) ** 2
        period_end = sample["ts"]
        period_begin = period_end - duration
        sample_count = 1
        actual_duration = 0

        while True: # Repeat .. Until
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                # we've exhausted the full buffer
                return None, None, None, None
            sample = self.get(next_offset)
            if sample == None:
                # we've exhausted the values in the partially filled buffer
                return None, None, None, None
            if sample["ts"] < period_begin:
                break
            total_variance += (sample["value"] - avg) ** 2
            sample_count += 1
            actual_duration = period_end - sample["ts"]

        # Using sample_count (not sample_count - 1) as divisor in case user wants deviation of 1 sample.
        deviation = (total_variance / sample_count) ** 0.5

        if self.settings["LOG_LEVEL"] == 1:
            print("deviation {} duration {} with {} samples".format(deviation, actual_duration, sample_count))

        return deviation, next_offset, actual_duration, sample_count

    # find(offset, duration, test_fn) returns tuple (sample,...) if 'test_fn(sample)' returns
    # True for any sample in buffer from 'offset' back for 'duration' seconds. Otherwise returns (None,...)
    # Parameters:
    #       offset: index offset (latest sample = 0, previous = 1 etc)
    #       duration: time in seconds over which to apply the 'test_fn(value)' function
    #       test_fn: a function which returns True or False for each buffer ts/value entry.
    # Returns tuple (sample, next_offset, actual_duration, sample_count)
    # where:
    #       sample = sample|None whether the required sample was found in buffer
    #       next_offset = offset in buffer of 1st sample older than value for which found=True (or duration)
    #       actual_duration = duration (seconds) from found value to newest within duration
    #       sample_count = how many buffer values were used in search for found value
    def find(self, offset, duration, test_fn):
        # lookup the first value to get that value and timestamp
        sample = self.get(offset)
        if sample is None:
            return None, None, None, None

        next_offset = offset
        period_end = sample["ts"]
        period_begin = period_end - duration
        sample_count = 0
        actual_duration = 0

        while sample["ts"] >= period_begin:
            sample_count += 1
            actual_duration = period_end - sample["ts"]

            # apply provided test function
            found = test_fn(sample)

            # We haven't found a matching value so move on to next sample in buffer
            # select previous index in circular buffer
            next_offset = (next_offset + 1) % self.SAMPLE_HISTORY_SIZE
            if next_offset == offset:
                next_offset = None
                break

            next_sample = self.get(next_offset)

            if next_sample == None:
                next_offset = None
                # we've exhausted the values in the partially filled buffer
                break

            if found:
                break

            sample = next_sample

        if self.settings["LOG_LEVEL"] == 1:
            print("TimeBuffer.find() {} duration {} with {} samples".format(found, actual_duration, sample_count))

        # A chance to use Python's quirky conditional expression syntax...
        return_sample = sample if found else None

        return return_sample, next_offset, actual_duration, sample_count

# -----------------------------------------------------------------------------------------
#
# StatsBuffer
#
# StatsBuffer is a sub-class of TimeBuffer which stores median / deviation for prior
# periods so they don't need to be re-computed e.g. within pattern tests.
#
# The StatsBuffer takes a 'duration (seconds)' instantiation parameter that defines the
# time over which stats should be collected, using a local TimeBuffer (self.value_buffer) to
# accumulate the necessary number of samples to calculate those stats. After a 'duration's-worth of
# samples are collected the StatsBuffer produces a 'stats' record of median and duration
# for those samples and 'put's this record into its TimeBuffer.
#
# Note the actual duration used for the calculation will be <= 'duration' due to the assumed
# stochastic nature of the values recorded. I.e. the stats will be from the latest sample going
# back in time to the earliest sample with a timestamp greater than (current timestamp - duration).
#
# The stats record is:
#     { "median": numeric median value of the value samples for thid duration
#       "deviation":
#       "duration": actual duration of this stats calculation, i.e current_ts - earliest_ts
#       "sample_count": how many samples were used in calculating these stats
#     }
#
# Note there are *two* TimeBuffers involved:
#   (1) The buffer provided by the parent class, which StatsBuffer uses to store the
#       'stats' values (<timestamp>, <stats record>)
#   (2) sample_buffer, given on instantiation, which is used to provide the latest duration's worth
#       of data samples to be used in calculating the stats record.
#
# The StatsBuffer.update() will create the stats record when sufficient
# time has passed such that the required data is available in the sample_buffer. This update()
# method can most simply be called each time a sample is added to the sample_buffer.
#
#
# -----------------------------------------------------------------------------------------

class StatsBuffer(TimeBuffer):

    # Initialize a new StatsBuffer object
    def __init__(self, size=100, duration=1, settings=None):

        self.settings = settings

        # initialize TimeBuffer
        super().__init__(size=size,settings=settings)

        self.duration = duration

        # initialize property to record start time of current stats period
        self.start_ts = None


    # Update this TimeBuffer if enough new data is available in the sample_buffer
    def update(self, sample_buffer):

        sample = sample_buffer.get(0)

        if sample is None:
            return

        ts = sample["ts"]

        # Initialize start_ts for the first stats peroid
        if self.start_ts is None:
            self.start_ts = ts

        elif ts > self.start_ts + self.duration:
            self.put_stats(sample_buffer)
            self.start_ts = ts


    # Add a new stats record to this TimeBuffer
    def put_stats(self, sample_buffer):

        sample = sample_buffer.get(0)

        if sample is None:
            return

        ts = sample["ts"]

        med, offset, duration, sample_count = sample_buffer.median(0, self.duration)
        dev, offset, duration, sample_count = sample_buffer.deviation(0, self.duration, med)

        stats_value = { "median": med,
                        "deviation": dev,
                        "duration": duration,
                        "sample_count": sample_count
                      }

        super().put(ts, stats_value)




