# -------------------------------------------------------------------
#
# Python script to run sensor
#
# -------------------------------------------------------------------

import sys

from sensor import Sensor

from config import Config

from sensor_utils import list_to_string

VERSION = "0.40"

# loads settings from sensor.json or argv[1]
CONFIG_FILENAME = "sensor_config.json"


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

if __name__ == "__main__":

    # Use default filename OR one given as argument
    filename = CONFIG_FILENAME

    print("main started with {} arguments {}".format(len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]

    config = Config(filename)

    s = Sensor(config)

    # Infinite loop until killed, reading weight and sending data
    interrupt_code = s.loop()

    # Cleanup and quit
    s.finish()

