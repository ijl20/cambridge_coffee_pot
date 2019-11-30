# -------------------------------------------------------------------
#
# Python script to run sensor
#
# -------------------------------------------------------------------

import sys
import time

from classes.sensor import Sensor

from classes.weight_sensor import WeightSensor

from classes.config import Config

from classes.sensor_utils import list_to_string

VERSION = "0.40"

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

if __name__ == "__main__":

    print("main started with {} arguments {}".format(len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    s = Sensor(settings = config.settings)

    weight_sensor = WeightSensor(config.settings)

    # Infinite loop until killed, reading weight and sending data
    try:
        while True:
            #----------------
            # GET READING
            # ---------------

            # get readings from all load cells
            value = weight_sensor.get_value()

            # ---------------
            # PROCESS READING
            # ---------------
            s.process_sample(time.time(), value)

            time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        pass

    # Cleanup and quit
    s.finish()

