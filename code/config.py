
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Startup config
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import simplejson as json

# These config valued proved defaults, as the config file will be merged in.
DEFAULT_CONFIG = {
    "LOG_LEVEL": 1, # 1 = debug, 2 = info
    # filename to persist scales tare values
    "TARE_FILENAME": "sensor_tare.json",
    "WEIGHT_FACTOR": 412, # reading per gram

    # LCD panel size in pixels (0,0) is top left
    "LCD_WIDTH": 160,                # LCD panel width in pixels
    "LCD_HEIGHT": 128,               # LCD panel height

    # Pixel size and coordinates of the 'Weight' display
    "WEIGHT_HEIGHT": 40,
    "WEIGHT_WIDTH": 160,
    "WEIGHT_COLOR_FG": "WHITE",
    "WEIGHT_COLOR_BG": "BLACK",
    "WEIGHT_X": 0,
    "WEIGHT_Y": 60,
    "WEIGHT_RIGHT_MARGIN": 10
    }


class Config(object):

    def __init__(self,filename):

        try:
            config_file_handle = open(filename, "r")
            file_text = config_file_handle.read()
            config_dictionary = json.loads(file_text)
            config_file_handle.close()
            # here's the clever bit... merge entries from file in to CONFIG dictionary
            self.settings = { **DEFAULT_CONFIG, **config_dictionary }
            print("Config loaded {} LOG_LEVEL={}".format(filename,self.settings["LOG_LEVEL"]))

        except Exception as e:
            print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(filename))
            print(e)


