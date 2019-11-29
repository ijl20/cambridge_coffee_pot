#! /usr/bin/python3

# code version

VERSION = "0.50"

# Python libs
import time
import sys
import simplejson as json
import requests
import math

GPIO_FAIL = False
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO_FAIL = True
    print("RPi.GPIO not loaded, running in SIMULATION_MODE")

# LCD display libs
if not GPIO_FAIL:
    from st7735_ijl20.st7735 import ST7735
else:
    from st7735_ijl20.st7735_emulator import ST7735_EMULATOR as ST7735

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 40)
DEBUG_FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 14)

# General utility function (like list_to_string)
from sensor_utils import list_to_string

from time_buffer import TimeBuffer

# declare globals
LCD = None # ST7735 LCD display chip

# Data for pattern recognition

SAMPLE_HISTORY_SIZE = 1000
EVENT_HISTORY_SIZE = 5 # keep track of the most recent 5 events sent to server

# COFFEE POT EVENTS

EVENT_NEW = "COFFEE_NEW"
EVENT_EMPTY = "COFFEE_EMPTY"
EVENT_POURED = "COFFEE_POURED"
EVENT_REMOVED = "COFFEE_REMOVED"
EVENT_GROUND = "COFFEE_GROUND"

debug_list = [ 1, 2, 3, 4] # weights from each load cell, for debug display on LCD

class Sensor(object):

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # __init__() called on startup
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def __init__(self, settings=None):
        global LCD
        global GPIO_FAIL

        self.SIMULATION_MODE = GPIO_FAIL

        self.settings = settings

        # times to control update of LCD and watchdog sends to platform
        self.prev_send_time = None
        self.prev_lcd_time = None

        # initialize the st7735 for LCD display
        LCD = self.init_lcd()

        self.sample_buffer = TimeBuffer(size=SAMPLE_HISTORY_SIZE, settings=self.settings)

        self.event_buffer = TimeBuffer(size=EVENT_HISTORY_SIZE, settings=self.settings)


    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # LCD code
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def init_lcd(self):
        t_start = time.process_time()

        LCD = ST7735()

        LCD.begin()

        image = Image.open('pot.bmp')
        #LCD.LCD_PageImage(image)
        LCD.display(image)

        print("init_lcd in {:.3f} sec.".format(time.process_time() - t_start))

        self.chart = LCD.add_chart()

        return LCD

    # -------------------------------------------------------------------
    # ------ DRAW NUMERIC VALUE ON LCD  ---------------------------------
    # -------------------------------------------------------------------
    def draw_value(self, value):
        # create a blank image to write the weight on
        image = Image.new( "RGB",
                           ( self.settings["WEIGHT_WIDTH"],
                             self.settings["WEIGHT_HEIGHT"]),
                           self.settings["WEIGHT_COLOR_BG"])

        draw = ImageDraw.Draw(image)

        # convert weight to string with fixed 5 digits including 1 decimal place, max 9999.9

        display_number = value

        if display_number >= 10000:
            display_number = 9999.9

        draw_string = "{:5.0f}".format(display_number) # 10 points for witty variable name

        # calculate x coordinate necessary to right-justify text
        string_width, string_height = draw.textsize(draw_string, font=FONT)

        # embed this number into the blank image we created earlier
        draw.text((self.settings["WEIGHT_WIDTH"]-string_width-self.settings["WEIGHT_RIGHT_MARGIN"],0),
                draw_string,
                fill = self.settings["WEIGHT_COLOR_FG"],
                font=FONT)

        # display image on screen at coords x,y. (0,0)=top left.
        LCD.display_window(image,
                        self.settings["WEIGHT_X"],
                        self.settings["WEIGHT_Y"],
                        self.settings["WEIGHT_WIDTH"],
                        self.settings["WEIGHT_HEIGHT"])

    # -------------------------------------------------------------------
    # ------ DRAW DEBUG READINGS ON LCD       ---------------------------
    # -------------------------------------------------------------------
    def draw_debug(self):
        # display a two-line debug display of the weights from both load cells
        if self.settings["LOG_LEVEL"] <= 2:
            image = Image.new("RGB", (160, 40), "BLACK")
            draw = ImageDraw.Draw(image)

            draw_string = "{:5.1f}".format(debug_list[0])
            draw.text((75,0), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[1])
            draw.text((75,20), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[2])
            draw.text((0,20), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[3])
            draw.text((0,0), draw_string, fill="YELLOW", font=DEBUG_FONT)

            LCD.display_window(image, 0, 40, 160, 40)

    # Update a PIL image with the weight, and send to LCD
    # Note we are creating an image smaller than the screen size, and only updating a part of the display
    def update_lcd(self, ts):
        global LCD

        t_start = time.process_time()

        if (self.prev_lcd_time is None) or (ts - self.prev_lcd_time > 1):
            sample_value, offset, sample_count = self.sample_buffer.median(0,1) # get median weight value for 1 second
            if not sample_value == None:
                self.draw_value(sample_value)

            self.prev_lcd_time = ts

            if self.settings["LOG_LEVEL"] == 1:
                if sample_value == None:
                    print("loop update_lcd skipped (None) at {:.3f} secs.".format(time.process_time() - t_start))
                else:
                    print("loop update_lcd {:.1f} at {:.3f} secs.".format(sample_value, time.process_time() - t_start))

            self.draw_debug()

        # -------------------------------------------------------------------
        # ------ ADD CURRENT WEIGHT TO BAR CHART   --------------------------
        # -------------------------------------------------------------------

        latest_sample = self.sample_buffer.get(0)
        if not latest_sample == None:
            # debug: need to link these constants to the actual bar settings...
            BAR_MAX_G = 5000
            BAR_MAX_Y = 40

            # Create a bar height proportional to the value, capped at bottom and top of chart.
            bar_height = math.floor(latest_sample["value"] / BAR_MAX_G * BAR_MAX_Y )

            if bar_height > BAR_MAX_Y:
                bar_height = BAR_MAX_Y
            elif bar_height < 1:
                bar_height = 1

            # This is a bar-per-sample. Could use time on x-axis.
            #self.chart.next(bar_height)
            self.chart.add_time(ts, bar_height)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # SEND DATA TO PLATFORM
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Post data to platform as json.
    # post_data is a python dictionary to be converted to json.
    def send_data(self, post_data):
        try:
            print("send_data() to {}".format(self.settings["FEEDMAKER_URL"]))
            if not self.SIMULATION_MODE:
                response = requests.post(
                        self.settings["FEEDMAKER_URL"],
                        headers={ self.settings["FEEDMAKER_HEADER_KEY"] : self.settings["FEEDMAKER_HEADER_VALUE"] },
                        json=post_data
                        )
                print("status code:",response.status_code)

            debug_str = json.dumps( post_data,
                                    sort_keys=True,
                                    indent=4,
                                    separators=(',', ': '))
            print("sent:\n {}".format(debug_str))
        except Exception as e:
            print("send_data() error with {}".format(post_data))
            print(e)

    def send_weight(self, ts, weight_g):
        post_data = {  'msg_type': 'coffee_pot_weight',
                    'request_data': [ { 'acp_id': self.settings["SENSOR_ID"],
                                        'acp_type': self.settings["SENSOR_TYPE"],
                                        'acp_ts': ts,
                                        'acp_units': 'GRAMS',
                                        'weight': math.floor(weight_g+0.5), # rounded to integer grams
                                        'version': VERSION
                                        }
                                    ]
                }
        self.send_data(post_data)

    def send_event(self, ts, event_code):
        post_data = { 'msg_type': 'coffee_pot_event',
                    'request_data': [ { 'acp_id': self.settings["SENSOR_ID"],
                                        'acp_type': self.settings["SENSOR_TYPE"],
                                        'acp_ts': ts,
                                        'event_code': event_code,
                                        'version': VERSION
                                        }
                                    ]
                }
        self.send_data(post_data)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # EVENT PATTERN RECOGNITION
    #
    # In general these routines look at the sample_history buffer and
    # decide if an event has just become recognizable, e.g. POT_NEW
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Test if pot is FULL
    # True if median for 1 second is 3400 grams +/- 400
    # Returns tuple <Test true/false>, < next offset >
    def test_full(self,offset):
        m, next_offset, sample_count = self.sample_buffer.median(offset, 1)
        if not m == None:
            return (abs(m - 3400) < 400), next_offset
        else:
            return None, None

    # Test if pot is REMOVED
    # True if median for 3 seconds is 0 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def test_removed(self,offset):
        m, next_offset, sample_count = self.sample_buffer.median(offset, 3)
        if not m == None:
            return (abs(m) < 100), next_offset
        else:
            return None, None

    def test_event_new(self, ts):
        full, offset = self.test_full(0)
        removed, new_offset = self.test_removed(offset)
        if removed and full:
            latest_event = self.event_buffer.get(0)
            if ((latest_event is None) or
               (latest_event["value"] != EVENT_NEW) or
               (ts - latest_event["ts"] > 600 )):
                return EVENT_NEW
            else:
                return None
        else:
            return None

    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    def test_event(self, ts):
        event = self.test_event_new(ts)
        if not event is None:
            self.event_buffer.put(ts, event)
            self.send_event(ts, event)
        return event

    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    #
    # process_sample(timestamp, value)
    #
    # Here is where we process each sensor sample, updating the LCD and checking for events
    #
    # --------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------
    def process_sample(self, ts, value):

        t_start = time.process_time()

        if self.settings["LOG_LEVEL"] == 1:
            print("process_sample got value {:.1f} at {:.3f} secs.".format(value, time.process_time() - t_start))

        # store weight and time in sample_history
        self.sample_buffer.put(ts, value)

        #----------------
        # UPDATE LCD
        # ---------------

        self.update_lcd(ts)

        # ----------------------
        # SEND EVENT TO PLATFORM
        # ----------------------

        self.test_event(ts)

        # ---------------------
        # SEND DATA TO PLATFORM
        # ---------------------

        if self.prev_send_time is None:
            self.prev_send_time = ts

        if ts - self.prev_send_time > 30:
            sample_value, offset, sample_count = self.sample_buffer.median(0,2) # from latest ts, back 2 seconds

            if not sample_value == None:
                print ("SENDING WEIGHT {:5.1f}, {}".format(sample_value, time.ctime(ts)))

                self.send_weight(ts, sample_value)

                self.prev_send_time = ts

                if self.settings["LOG_LEVEL"] == 1:
                    print("process_sample send data at {:.3f} secs.".format(time.process_time() - t_start))
            else:
                print("process_sample send data NOT SENT as data value None")

        if self.settings["LOG_LEVEL"] == 1:
            print ("WEIGHT {:5.1f}, {}".format(value, time.ctime(ts)))

        if self.settings["LOG_LEVEL"] == 1:
            print("process_sample time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # finish() - cleanup and exit if main loop is interrupted
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def finish(self):
        print("\n")

        if not self.SIMULATION_MODE:

            LCD.cleanup()

            print("GPIO cleanup()...")

            GPIO.cleanup()

            print("Exitting")

            sys.exit()

