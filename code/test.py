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

s = Sensor(settings = config.settings)

# for playback we can specify
#   sleep=0.1 for a fixed period between samples
# or
#   realtime=True which will pause the time between recorded sample timestamps.
# otherwise the playback will be as fast as possible.

t = TimeBuffer(settings=config.settings)

t.load('../data/2019-11-22_readings.csv')

t.play(s.process_sample, realtime=True)

