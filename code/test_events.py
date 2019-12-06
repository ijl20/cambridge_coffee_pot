import sys

from classes.time_buffer import TimeBuffer

from classes.config import Config

from classes.sensor import Sensor

from classes.sensor_utils import list_to_string

print("test.py started with {} arguments: [{}]".format(len(sys.argv), list_to_string(sys.argv)))

if len(sys.argv) > 1 :
    filename = sys.argv[1]
    config = Config(filename)
else:
    config = Config(None)

config.settings["VERSION"] = "TEST_0.1"

s = Sensor(settings = config.settings)

s.begin()

# for playback we can specify
#   sleep=0.1 for a fixed period between samples
# or
#   realtime=True which will pause the time between recorded sample timestamps.
# otherwise the playback will be as fast as possible.

t = TimeBuffer(size=140000,settings=config.settings)

#t.load('../../cambridge_coffee_pot_data/2019-12-04_pour_missed.csv')
#t.load('../../cambridge_coffee_pot_data/2019-12-04_full_pour.csv')
t.load('../../cambridge_coffee_pot_data/2019-12-04_full_day.csv')

t.play(s.process_sample)

