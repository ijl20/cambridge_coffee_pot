#! /usr/bin/python3

# code version

VERSION = "0.40"

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

# D to A converter libs
from hx711_ijl20.hx711 import HX711

# LCD display libs
from st7735_ijl20.st7735 import ST7735

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
hx_list = None # LIST of hx711 A/D chips

SAMPLE_BUFFER_SIZE = 100

# COFFEE POT EVENTS

EVENT_NEW = "COFFEE_NEW"
EVENT_EMPTY = "COFFEE_EMPTY"
EVENT_TAKEN = "COFFEE_TAKEN"
EVENT_REMOVED = "COFFEE_REMOVED"

EVENT_HISTORY_SIZE = 5 # keep track of the most recent 5 events sent to server
event_history = [ None ] * EVENT_HISTORY_SIZE

debug_list = [ 1, 2, 3, 4] # weights from each load cell, for debug display on LCD

class Sensor(object):

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # __init__() called on startup
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def __init__(self, config):
        global LCD
        global hx_list
        global GPIO_FAIL

        self.SIMULATION_MODE = GPIO_FAIL

        self.setting = config.setting

        now = time.time()  # floating point seconds in epoch

        # times to control update of LCD and watchdog sends to platform
        self.prev_send_time = now
        self.prev_lcd_time = now

        # initialize the st7735 for LCD display
        LCD = self.init_lcd()

        # initialize the two hx711 A/D converters
        hx_list = self.init_scales()

        # find the scales 'zero' reading
        self.tare_scales(hx_list)

        self.reading_buffer = TimeBuffer(SAMPLE_BUFFER_SIZE)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # HX711 A/D converter for load cells
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Initialize scales, return hx711 objects
    # Note there are TWO load cells, each with their own HX711 A/D converter.
    # Each HX711 has an A and a B channel, we are only using the A channel of each.
    def init_scales(self):

        t_start = time.process_time()

        # initialize HX711 objects for each of the load cells
        hx_list = [ HX711(5, 6),
                    HX711(12, 13),
                    HX711(19, 26),
                    HX711(16, 20)
                ]

        if self.setting["LOG_LEVEL"] == 1:
            print("init_scales HX objects created at {:.3f} secs.".format(time.process_time() - t_start))


        for hx in hx_list:

            # here we optionally set the hx711 library to give debug output
            #hx.DEBUG_LOG = DEBUG_LOG

            # set_reading_format(order bytes to build the "long" value, order of the bits inside each byte) MSB | LSB
            # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
            hx.set_reading_format("MSB", "MSB")

            hx.set_reference_unit_A(1)

            hx.reset()

        if self.setting["LOG_LEVEL"] == 1:
            print("init_scales HX objects reset at {:.3f} secs.".format(time.process_time() - t_start))

        return hx_list

    # Read the TARE_FILENAME defined in CONFIG, return the contained json as a python dictionary
    def read_tare_file(self):
        # if there is an existing tare file, previous values will be read from that
        if self.setting["LOG_LEVEL"] == 1:
            print("reading tare file {}".format(self.setting["TARE_FILENAME"]))

        try:
            tare_file_handle = open(self.setting["TARE_FILENAME"], "r")
            file_text = tare_file_handle.read()
            tare_dictionary = json.loads(file_text)
            tare_file_handle.close()
            print("LOADED TARE FILE {}".format(self.setting["TARE_FILENAME"]))
            return tare_dictionary
        except Exception as e:
            print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(self.setting["TARE_FILENAME"]))
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
            tare_file_handle = open(self.setting["TARE_FILENAME"], "w")
            tare_file_handle.write(tare_json)
            tare_file_handle.close()
        except:
            print("tare scales file write to tare json file {}".format(self.setting["TARE_FILENAME"]))

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
            tare_delta = abs(tare_list[i] - self.setting["TARE_READINGS"][i])
            if tare_delta > max_delta:
                max_delta = tare_delta
                max_i = i
            tare_delta_total += tare_delta
            if tare_delta > self.setting["TARE_WIDTH"]:
                if self.setting["LOG_LEVEL"] == 1:
                    print("tare_ok reading[{}] {:.0f} out of range vs {:.0f} +/- {}".format(i,
                        tare_list[i],
                        self.setting["TARE_READINGS"][i],
                        self.setting["TARE_WIDTH"]))

                return False
            else:
                i += 1

        if tare_delta_total > self.setting["TARE_WIDTH"] * 2:
            if self.setting["LOG_LEVEL"] == 1:
                print("tare_ok total delta {} of [{}] is out of range for [{}] +/- (2*){}".format(tare_delta_total,
                    list_to_string(tare_list,"{:+.0f}"),
                    list_to_string(self.setting["TARE_READINGS"],"{:+.0f}"),
                    self.setting["TARE_WIDTH"]))

            return False

        if self.setting["LOG_LEVEL"] == 1:
            print("tare_ok is OK, max delta[{}] was {:.0f}".format(max_i, max_delta))

        return True

    # Find the 'tare' for load cell 1 & 2
    def tare_scales(self,hx_list):

        t_start = time.process_time()

        tare_list = []

        # we 'tare' each sensor, this will also update the tare value used in each HX771 object
        for hx in hx_list:
            # Here we initialize the 'empty weight' settings
            tare_list.append( hx.tare_A() )

        if self.setting["LOG_LEVEL"] == 1:
            print("tare_scales readings [ {} ] completed at {:.3f} secs.".format( list_to_string(tare_list, "{:+.0f}"),
                                                                                time.process_time() - t_start))

        # If the tare_list is 'ok' (i.e. within bounds) we will write it to the tare file and return it as the result
        if self.tare_ok(tare_list):
            self.write_tare_file(tare_list)
            return tare_list

        # Otherwise.. the tare reading was NOT ok...
        # The new tare readings are out of range, so use persisted values
        tare_dictionary = self.read_tare_file()

        tare_list = tare_dictionary["tares"]

        # As the measured tare values are not acceptable, we now update the HX711 objects with the persisted values.
        i = 0
        for hx in hx_list:
            hx.set_offset_A(tare_list[i])
            i += 1

        if self.setting["LOG_LEVEL"] == 1:
            output_string = "tare_scales readings out of range, using persisted values [ {} ]"
            print(output_string.format(list_to_string(tare_list,"{:+.0f}")))

        return tare_list

    # Return the weight in grams, combined from both load cells
    def get_weight(self):
        global hx_list
        global debug_list

        debug_list = []

        t_start = time.process_time()

        total_reading = 0

        for hx in hx_list:
            # get_weight accepts a parameter 'number of times to sample weight and then average'
            reading = hx.get_weight_A(1)
            debug_list.append(reading) # store weight for debug display
            total_reading = total_reading + reading

        if self.setting["LOG_LEVEL"] == 1:
            output_string = "get_weight readings [ {} ] completed at {:.3f} secs."
            print( output_string.format(list_to_string(debug_list, "{:+.0f}"), time.process_time() - t_start))

        return total_reading / self.setting["WEIGHT_FACTOR"] # grams


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

        if self.setting["LOG_LEVEL"] == 1:
            print("init_lcd in {:.3f} sec.".format(time.process_time() - t_start))

        return LCD

    # Update a PIL image with the weight, and send to LCD
    # Note we are creating an image smaller than the screen size, and only updating a part of the display
    def update_lcd(self, weight_g):
        global LCD

        t_start = time.process_time()

        # create a blank image to write the weight on
        image = Image.new( "RGB",
                           ( self.setting["WEIGHT_WIDTH"],
                             self.setting["WEIGHT_HEIGHT"]),
                           self.setting["WEIGHT_COLOR_BG"])

        draw = ImageDraw.Draw(image)

        # convert weight to string with fixed 5 digits including 1 decimal place, max 9999.9

        display_number = weight_g

        if display_number >= 10000:
            display_number = 9999.9

        draw_string = "{:5.1f}".format(display_number) # 10 points for witty variable name

        # calculate x coordinate necessary to right-justify text
        string_width, string_height = draw.textsize(draw_string, font=FONT)

        # embed this number into the blank image we created earlier
        draw.text((self.setting["WEIGHT_WIDTH"]-string_width-self.setting["WEIGHT_RIGHT_MARGIN"],0),
                draw_string,
                fill = self.setting["WEIGHT_COLOR_FG"],
                font=FONT)

        # display image on screen at coords x,y. (0,0)=top left.
        LCD.display_window(image,
                        self.setting["WEIGHT_X"],
                        self.setting["WEIGHT_Y"],
                        self.setting["WEIGHT_WIDTH"],
                        self.setting["WEIGHT_HEIGHT"])

        # display a two-line debug display of the weights from both load cells
        if self.setting["LOG_LEVEL"] == 1:
            image = Image.new("RGB", (150, 40), "BLACK")
            draw = ImageDraw.Draw(image)

            draw_string = "{:5.1f}".format(debug_list[0])
            draw.text((75,0), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[1])
            draw.text((75,20), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[2])
            draw.text((0,20), draw_string, fill="YELLOW", font=DEBUG_FONT)

            draw_string = "{:5.1f}".format(debug_list[3])
            draw.text((0,0), draw_string, fill="YELLOW", font=DEBUG_FONT)

            LCD.display_window(image, 5, 5, 150, 40)

        if self.setting["LOG_LEVEL"] == 1:
            print("LCD updated with weight {:.1f} in {:.3f} secs.".format(display_number, time.process_time() - t_start))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # SEND DATA TO PLATFORM
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    # Post data to platform as json.
    # post_data is a python dictionary to be converted to json.
    def send_data(self, post_data):
        try:
            print("send_data() to {}".format(self.setting["FEEDMAKER_URL"]))
            if not self.SIMULATION_MODE:
                response = requests.post(
                        self.setting["FEEDMAKER_URL"],
                        headers={ self.setting["FEEDMAKER_HEADER_KEY"] : self.setting["FEEDMAKER_HEADER_VALUE"] },
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

    def send_weight(self, weight_g):
        now = time.time()
        post_data = {  'msg_type': 'coffee_pot_weight',
                    'request_data': [ { 'acp_id': self.setting["SENSOR_ID"],
                                        'acp_type': self.setting["SENSOR_TYPE"],
                                        'acp_ts': now,
                                        'acp_units': 'GRAMS',
                                        'weight': math.floor(weight_g+0.5), # rounded to integer grams
                                        'version': VERSION
                                        }
                                    ]
                }
        self.send_data(post_data)

    def send_event(self, event_code):
        now = time.time()
        post_data = {  'msg_type': 'coffee_pot_event',
                    'request_data': [ { 'acp_id': self.setting["SENSOR_ID"],
                                        'acp_type': self.setting["SENSOR_TYPE"],
                                        'acp_ts': now,
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
        m, next_offset = self.reading_buffer.median(offset, 1)
        if not m == None:
            return (abs(m - 3400) < 400), next_offset
        else:
            return None, None

    # Test if pot is REMOVED
    # True if median for 3 seconds is 0 grams +/- 100
    # Returns tuple <Test true/false>, < next offset >
    def test_removed(self,offset):
        m, next_offset = self.reading_buffer.median(offset, 3)
        if not m == None:
            return (abs(m) < 100), next_offset
        else:
            return None, None

    def test_new(self):
        full, offset = self.test_full(0)
        removed, new_offset = self.test_removed(offset)
        if removed and full:
            print("NEW POT EVENT")

    # Look in the sample_history buffer (including latest) and try and spot a new event.
    # Uses the event_history buffer to avoid repeated messages for the same event
    def test_event(self):
        self.test_new()
        return

    def process_sample(self, ts, value):

        t_start = time.process_time()


        if self.setting["LOG_LEVEL"] == 1:
            print("loop got weight {:.1f} at {:.3f} secs.".format(value, time.process_time() - t_start))

        # store weight and time in sample_history
        self.reading_buffer.put(ts, value)

        #----------------
        # UPDATE LCD
        # ---------------

        now = time.time()
        if now - self.prev_lcd_time > 1:
            sample_value, offset = self.reading_buffer.median(0,1) # get median weight value for 1 second
            if not sample_value == None:
                self.update_lcd(sample_value)

            self.prev_lcd_time = now

            if self.setting["LOG_LEVEL"] == 1:
                if sample_value == None:
                    print("loop update_lcd skipped (None) at {:.3f} secs.".format(time.process_time() - t_start))
                else:
                    print("loop update_lcd {:.1f} at {:.3f} secs.".format(sample_value, time.process_time() - t_start))

        # ----------------------
        # SEND EVENT TO PLATFORM
        # ----------------------

        self.test_event()

        # ---------------------
        # SEND DATA TO PLATFORM
        # ---------------------

        now = time.time() # floating point time in seconds since epoch
        if now - self.prev_send_time > 30:
            sample_value, offset = self.reading_buffer.median(0,2) # from NOW, back 2 seconds

            if not sample_value == None:
                print ("SENDING WEIGHT {:5.1f}, {}".format(sample_value, time.ctime(now)))

                self.send_weight(sample_value)

                self.prev_send_time = now

                if self.setting["LOG_LEVEL"] == 1:
                    print("loop send data at {:.3f} secs.".format(time.process_time() - t_start))
            else:
                print("loop send data NOT SENT as data value None")

        if self.setting["LOG_LEVEL"] == 1:
            print ("WEIGHT {:5.1f}, {}".format(value, time.ctime(now)))

        #hx.power_down()
        #hx.power_up()

        if self.setting["LOG_LEVEL"] == 1:
            print("loop time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # finish() - cleanup and exit if main loop is interrupted
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

    def finish(self):
        print("\n")

        print("GPIO cleanup()...")

        if not self.SIMULATION_MODE:
            GPIO.cleanup()

            print("Exitting")

            sys.exit()

