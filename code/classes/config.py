
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Startup config
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

import simplejson as json

# loads settings from sensor.json or argv[1]
CONFIG_FILENAME = "config/sensor_config.json"

class Config(object):

    def __init__(self,filename=None):

        try:
            # Always load "sensor_config.json"
            prod_file_handle = open(CONFIG_FILENAME, "r")
            prod_text = prod_file_handle.read()
            prod_dictionary = json.loads(prod_text)
            prod_file_handle.close()

            if not filename is None:
                # But overlay with values from given filename
                config_file_handle = open(filename, "r")
                file_text = config_file_handle.read()
                config_dictionary = json.loads(file_text)
                config_file_handle.close()
            else:
                config_dictionary = {}

            # here's the clever bit... merge entries from file in to CONFIG dictionary
            self.settings = { **prod_dictionary, **config_dictionary }
            print("Config loaded {} LOG_LEVEL={}".format(filename,self.settings["LOG_LEVEL"]))

        except Exception as e:
            print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(filename))
            print(e)


