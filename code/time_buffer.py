
class TimeBuffer(object):

    def __init__(self, size):
        print("TimeBuffer init")
                # Note sample_history is a *circular* buffer (for efficiency)
        self.SAMPLE_HISTORY_SIZE = size # store weight samples 0..(size-1)
        self.sample_history_index = 0
        self.sample_history = [ None ] * self.SAMPLE_HISTORY_SIZE # buffer for 100 weight samples ~= 10 seconds

    # sample_history: global circular buffer containing { ts:, weight:} datapoints
    # sample_history_index: global giving INDEX into buffer for NEXT datapoint

    # store the current weight in the sample_history circular buffer
    def record_sample(self, weight_g):
        self.sample_history[self.sample_history_index] = { 'ts': time.time(), 'weight': weight_g }
        if CONFIG["LOG_LEVEL"] == 1:
            print("record sample_history[{}]:\n{},{}".format(self.sample_history_index,
                                                        self.sample_history[self.sample_history_index]["ts"],
                                                        self.sample_history[self.sample_history_index]["weight"]))

        self.sample_history_index = (self.sample_history_index + 1) % self.SAMPLE_HISTORY_SIZE

    # Lookup the weight in the sample_history buffer at offset before now (offset ZERO = latest weight)
    # This returns None or an object { 'ts': <timestamp>, 'weight': <grams> }
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
                                        self.sample_history[index]["weight"]))
            else:
                debug_str = "lookup_sample None @ current {}, offset {} => {}"
                print(debug_str.format( self.sample_history_index,
                                        offset,
                                        index))
        return self.sample_history[index]

    # Iterate backwards through sample_history buffer to find index
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

    # Calculate the average weight recorded over the previous 'duration' seconds from time_offset seconds.
    # Returns a tuple of <average weight>, <index> where <index> is the sample_history offset
    # one sample earlier than the offset & duration selected.
    # E.g. average_time(0,3) will find the average weight of the most recent 3 seconds.
    def average_time(self, time_offset, duration):
        if CONFIG["LOG_LEVEL"] == 1:
            print("average_time time_offset={}, duration={}".format(time_offset, duration))

        offset = self.time_to_offset(time_offset)

        # lookup the first weight to get that weight (grams) and timestamp
        sample = self.lookup_sample(offset)
        if sample == None:
            return None, offset

        next_offset = offset
        total_weight = sample["weight"]
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
            total_weight += sample["weight"]
            sample_count += 1

        return total_weight / sample_count, next_offset

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
        begin_time = sample["ts"] # this will be updated as we loop, to find duration available
        end_time = sample["ts"]

        #if CONFIG["LOG_LEVEL"] == 1:
        #    print("weight_median begin_time {:.3f}".format(begin_time))

        weight_list = [ sample["weight"] ]
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

            begin_time = sample["ts"]
            #if CONFIG["LOG_LEVEL"] == 1:
            #    print("weight_median end_time {:.3f}".format(begin_time))

            weight_list.append(sample["weight"])

            if sample["ts"] < begin_limit:
                break

        # If we didn't get enough samples, return with error
        if len(weight_list) < 3:
            print("median_time not enough samples ({})".format(len(weight_list)))
            return None, None

        # Now we have a list of samples with the required duration
        med = median(weight_list)

        if CONFIG["LOG_LEVEL"] == 1:
            print("weight_median for {:.3f} seconds with {} samples = {}".format(end_time - begin_time, len(weight_list), med))

        return med, next_offset
