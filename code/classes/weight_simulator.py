# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Weight Simulator
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import time
import simplejson as json
from datetime import datetime

from classes.time_buffer import TimeBuffer

class WeightSimulator(object):
    def __init__(self, settings=None, filename="../data/test_fill.csv"):

        self.settings = settings

        t_start = time.process_time()

        print("WeightSimulator init")

        self.sample_buffer = TimeBuffer(size=12000,settings=self.settings)

        self.sample_buffer.load(filename)

        # Get the Unix timestamp from the latest entry in the buffer
        start_ts = self.sample_buffer.get(0)["ts"]
        start_ts_str = datetime.utcfromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')

        print("WeightSimulator loaded {} samples from {} up to {}".format(self.sample_buffer.samples,
                                                                          filename,
                                                                          start_ts_str))

        # Set flag so we recognize first get request, and can adjust time from there
        self.first_get = True

    # Return the weight in grams, combined from both load cells
    def get_value(self, ts=time.time()):

        # On first get, we'll calculate the time delta from 'real' now to the first sample
        # so we can play the data at the right speed
        if self.first_get:
            self.first_get = False
            self.sample_offset = self.sample_buffer.samples - 1
            self.current_sample = self.sample_buffer.get(self.sample_offset)
            self.current_ts = self.current_sample["ts"]
            self.time_delta = ts - self.current_ts
            weight = self.current_sample["value"]
        else:
            self.sample_offset -= 1
            if self.sample_offset < 0:
                weight = 0.0
            else:
                self.current_sample = self.sample_buffer.get(self.sample_offset)
                weight = self.current_sample["value"]

        #print("WeightSimulator {:.3f} returning {}".format(self.current_sample["ts"], weight))

        return weight

