
from sensor_utils import TimeBuffer

from config import Config

from sensor import Sensor

t = TimeBuffer()

t.load('../data/2019-11-22_readings.csv')

c = Config('sensor_config.json')

s = Sensor(c)

t.play(s.process_sample)
