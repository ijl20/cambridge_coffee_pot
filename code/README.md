# Python Smart Sensor Framework

This framework is designed for sensors that send their data back in real-time, to be processed immediately in
the receiving system.

## Key concepts:

*readings*: The actual sensor measurements, taken as frequently as is reasonable. I.e. the sensor will typically
be able to measure stuff more frequently than it might be expected to send it back to a server. Most sensors today
periodically (once a second, once a minute, once an hour, or whatever) send their most recent reading (or some
average, or other derived value) back to a server where it can be stored for programs or people later to look at
it.

*events*: This is the essential advance in the framework, with the expectation the sensor is designed to be
smart enough to recognize meaningful situations reflected by the sensor readings. Examples for the Cambridge
Coffee Pot include a new pot of coffee, or the pot becoming empty, or someone taking a cup of coffee from the
pot. These events can be transmitted *immediately* in contrast to the generic 'sensor readings' which may be
reported periodically.

*feedhandler*: This is a component of the receiving application system that is designed to process the
incoming data (particularly the *events*) in real-time. I.e. there is no delay built into the system as a
result of the receiving application simply *storing* the data in the hope that some subsequent process will
query the data and process it. The vast majority of existing systems process incoming data by storing it (e.g.
a customer order, a traffic light failure report), with separate program periodically checking to see if any
customers have ordered anything or any traffic lights have been reported broken.

## main.py

Provides the outermost application code which instantiates the required classes (i.e. Config, Sensor)
and loops loading sensor readings and processes each reading.

## config.py

Creates a Config() object with a 'settings' dictionary with values loaded from a provided filename.

## sensor.py

Links to the required libraries and reads the data from the sensors.

Stores the loaded data in a TimeBuffer.

Provides the `process_sample` function to process the data, which will look at the current value and
also some range of previous values to decide whether an EVENT has occurred.

## sensor_utils.py

Contains generally useful functions and classes, particularly TimeBuffer, see below.

### TimeBuffer

E.g. with `buffer = TimeBuffer(1000)`:

The argument to TimeBuffer is `size` i.e. how many entries you wish to store before the buffer wraps.

Implements a circular buffer of *time*, *value* pairs which can be stored with `buffer.put(ts,value)`
and retrieved with `buffer.get(offset)` where `offset` is an index *offset* into the buffer from the
latest reading.

The latest sample reading can always be retrieved at `buffer.get(0)`, and the immediate previous reading will
be `buffer.get(1)` etc.

TimeBuffer contains generally useful functions such as `median(offset, duration)` which will return the median
value for the readings in the buffer between the reading at the index `offset` from the latest reading, and extending
back `duration` seconds before that reading.

## Sample replay of data

See `test.py`

```
Python 3.6.8 (default, Oct  7 2019, 12:59:55)
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.

>>> from sensor_utils import TimeBuffer

>>> t = TimeBuffer()
TimeBuffer init size=1000

>>> from sensor import Sensor
RPi.GPIO not loaded, running in SIMULATION_MODE

>>> from config import Config

>>> c = Config('sensor_debug.json')
Config loaded sensor_debug.json LOG_LEVEL=1

>>> s = Sensor(c)
initializing LCD_ST7735
init_lcd in 0.011 sec.
init_scales HX objects created at 0.000 secs.
init_scales HX objects reset at 0.000 secs.
tare_scales readings [ +7, +7, +7, +7 ] completed at 0.000 secs.
tare_ok reading[0] 7 out of range vs -504000 +/- 100000
reading tare file sensor_tare.json
LOADED TARE FILE sensor_tare.json
tare_scales readings out of range, using persisted values [ -503886, +430966, -213330, +568053 ]
TimeBuffer init size=100

>>> t.load('../data/2019-11-22_readings.csv')

>>> t.play(s.process_sample)
```
