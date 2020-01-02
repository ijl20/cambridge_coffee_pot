# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Weight Sensor
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import time
import simplejson as json
from hx711_ijl20.hx711 import HX711

from classes.sensor_utils import list_to_string

class WeightSensor(object):
    """
        Instantiation:
            weight_sensor = WeightSensor(settings=settings)

        Methods:
            weight_sensor.get_value() # returns weight in grams
    """

    # Initialize scales, return hx711 objects
    # Note there are TWO load cells, each with their own HX711 A/D converter.
    # Each HX711 has an A and a B channel, we are only using the A channel of each.
    def __init__(self, settings=None):

        self.settings = settings

        t_start = time.process_time()

        # initialize HX711 objects for each of the load cells
        self.hx_list = [ HX711(5, 6),
                        HX711(12, 13),
                        HX711(19, 26),
                        HX711(16, 20)
                       ]

        if self.settings["LOG_LEVEL"] == 1:
            print("init_scales HX objects created at {:.3f} secs.".format(time.process_time() - t_start))


        for hx in self.hx_list:

            # here we optionally set the hx711 library to give debug output
            #hx.DEBUG_LOG = DEBUG_LOG

            # set_reading_format(order bytes to build the "long" value, order of the bits inside each byte) MSB | LSB
            # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
            hx.set_reading_format("MSB", "MSB")

            hx.set_reference_unit_A(1)

            hx.reset()

        self.tare_scales()

        if self.settings["LOG_LEVEL"] == 1:
            print("init_scales HX objects reset at {:.3f} secs.".format(time.process_time() - t_start))


    # Read the TARE_FILENAME defined in CONFIG, return the contained json as a python dictionary
    def read_tare_file(self):
        # if there is an existing tare file, previous values will be read from that
        if self.settings["LOG_LEVEL"] == 1:
            print("reading tare file {}".format(self.settings["TARE_FILENAME"]))

        try:
            tare_file_handle = open(self.settings["TARE_FILENAME"], "r")
            file_text = tare_file_handle.read()
            tare_dictionary = json.loads(file_text)
            tare_file_handle.close()
            print("LOADED TARE FILE {}".format(self.settings["TARE_FILENAME"]))
            return tare_dictionary
        except Exception as e:
            print("READ TARE FILE ERROR. Can't read supplied filename {}".format(self.settings["TARE_FILENAME"]))
            print(e)

        return {}

    # Write the tare_list and current timestamp as json into the file TARE_FILENAME defined in CONFIG
    def write_tare_file(self,tare_list):
        acp_ts = time.time() # epoch time in floating point seconds

        tare_json = """
        {{ "acp_ts": {:.3f},
            "tares": [ {:.1f}, {:.1f}, {:.1f}, {:1f} ]
        }}
        """.format(acp_ts, *tare_list)

        try:
            tare_file_handle = open(self.settings["TARE_FILENAME"], "w")
            tare_file_handle.write(tare_json)
            tare_file_handle.close()
        except:
            print("tare scales file write to tare json file {}".format(self.settings["TARE_FILENAME"]))

    # Return True if the latest tare readings are within the bounds set in CONFIG.
    # This is designed to ensure we don't 'tare' with the pot sitting on the sensor.
    def tare_ok(self,tare_list):
        i = 0
        # We compare each value in the tare_list and see if it is within the allowed TARE_WIDTH
        # of the corresponding approximate expected reading in TARE_READINGS. Also the total
        # of the readings must be within the config total +/- * TARE_WIDTH * 2.
        # We will only return True if *all* tare readings and the tare_total are within acceptable bounds.
        tare_delta_total = 0
        max_delta = 0 # we track max delta for debug purposes
        max_i = 0
        while i < len(tare_list):
            tare_delta = tare_list[i] - self.settings["TARE_READINGS"][i]
            if abs(tare_delta) > max_delta:
                max_delta = tare_delta
                max_i = i
            tare_delta_total += tare_delta
            if abs(tare_delta) > self.settings["TARE_WIDTH"]:
                if self.settings["LOG_LEVEL"] <= 2:
                    print("tare_ok FAIL reading[{}] {:.0f} out of range vs {:.0f} +/- {}".format(i,
                        tare_list[i],
                        self.settings["TARE_READINGS"][i],
                        self.settings["TARE_WIDTH"]))

                return False
            else:
                i += 1

        if tare_delta_total > self.settings["TARE_WIDTH"]:
            if self.settings["LOG_LEVEL"] == 1:
                print("tare_ok total delta {} of [{}] is out of range for [{}] +/- {}".format(tare_delta_total,
                    list_to_string(tare_list,"{:+.0f}"),
                    list_to_string(self.settings["TARE_READINGS"],"{:+.0f}"),
                    self.settings["TARE_WIDTH"]))

            return False

        if self.settings["LOG_LEVEL"] == 1:
            print("tare_ok is OK, max delta[{}] was {:.0f}".format(max_i, max_delta))

        return True

    # Find the 'tare' for load cell 1 & 2
    def tare_scales(self):

        t_start = time.process_time()

        tare_list = []

        # we 'tare' each sensor, this will also update the tare value used in each HX771 object
        for hx in self.hx_list:
            # Here we initialize the 'empty weight' settings
            tare_list.append( hx.tare_A() )

        print("tare_scales readings [ {} ] completed at {:.3f} secs.".format( list_to_string(tare_list, "{:+.0f}"),
                                                                                time.process_time() - t_start))

        # If the tare_list is 'ok' (i.e. within bounds) we will write it to the tare file and return it as the result
        if self.tare_ok(tare_list):
            print("tare_scales updating tare file.")
            self.write_tare_file(tare_list)
            return tare_list

        # Otherwise.. the tare reading was NOT ok...
        # The new tare readings are out of range, so use persisted values
        tare_dictionary = self.read_tare_file()

        tare_list = tare_dictionary["tares"]

        # As the measured tare values are not acceptable, we now update the HX711 objects with the persisted values.
        i = 0
        for hx in self.hx_list:
            hx.set_offset_A(tare_list[i])
            i += 1

        output_string = "tare_scales readings out of range, using persisted values [ {} ]"
        print(output_string.format(list_to_string(tare_list,"{:+.0f}")))

        return tare_list

    # Return the weight in grams, combined from both load cells
    def get_value(self):
        t_start = time.process_time()

        total_reading = 0
        reading_list = []
        for hx in self.hx_list:
            # get_weight accepts a parameter 'number of times to sample weight and then average'
            reading = hx.get_weight_A(1)
            reading_list.append(reading)
            total_reading = total_reading + reading

        if self.settings["LOG_LEVEL"] == 1:
            output_string = "get_weight readings [ {} ] completed at {:.3f} secs."
            print( output_string.format(list_to_string(reading_list, "{:+.0f}"), time.process_time() - t_start))

        return total_reading / self.settings["WEIGHT_FACTOR"] # grams

