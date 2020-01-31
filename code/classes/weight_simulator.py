# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Weight Simulator
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import time
import simplejson as json

from classes.utils import list_to_string

class WeightSimulator(object):
    def __init__(self, settings=None):

        self.settings = settings

        t_start = time.process_time()

        print("WeightSimulator init")


    # Return the weight in grams, combined from both load cells
    def get_value(self):

        return 2500.0

