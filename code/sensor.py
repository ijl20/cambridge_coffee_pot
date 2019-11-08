#! /usr/bin/python3

# for dev / debug
DEBUG_LOG = True

# loads settings from sensor.json or argv[1]
CONFIG_FILENAME = "sensor_config.json"

# Python libs
import time
import sys
import RPi.GPIO as GPIO
import simplejson as json
import requests

# D to A converter libs
from hx711_ijl20.hx711 import HX711

# LCD display libs
from st7735_ijl20.st7735 import ST7735

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

# General utility function (like list_to_string)
from sensor_utils import UTILS
u = UTILS()

FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 40)
DEBUG_FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 14)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Startup config
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

# These config valued proved defaults, as the config file will be merged in.
CONFIG = {
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

# Load sensor configuration from Json config file
def load_config():
    filename = CONFIG_FILENAME
    try:
        if len(sys.argv) > 1 and sys.argv[1]:
            filename = sys.argv[1]

        read_config_file(filename)

    except Exception as e:
        print("load_config exception {}".format(filename))
        print(e)
        pass

def read_config_file(filename):
    global CONFIG
    if DEBUG_LOG:
        print("reading config file {}".format(filename))

    try:
        config_file_handle = open(filename, "r")
        file_text = config_file_handle.read()
        config_dictionary = json.loads(file_text)
        config_file_handle.close()
        # here's the clever bit... merge entries from file in to CONFIG dictionary
        CONFIG = { **CONFIG, **config_dictionary }
    except Exception as e:
        print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(filename))
        print(e)



# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# HX711 A/D converter for load cells
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

# Initialize scales, return hx711 objects
# Note there are TWO load cells, each with their own HX711 A/D converter.
# Each HX711 has an A and a B channel, we are only using the A channel of each.
def init_scales():

    t_start = time.process_time()

    # initialize HX711 objects for each of the load cells
    hx_list = [ HX711(5, 6),
                HX711(12, 13),
                HX711(19, 26),
                HX711(16, 20)
              ]

    if DEBUG_LOG:
        print("init_scales HX objects created at {:.3f} secs.".format(time.process_time() - t_start))


    for hx in hx_list:

        # here we optionally set the hx711 library to give debug output
        #hx.DEBUG_LOG = DEBUG_LOG

        # set_reading_format(order bytes to build the "long" value, order of the bits inside each byte) MSB | LSB
        # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
        hx.set_reading_format("MSB", "MSB")

        hx.set_reference_unit_A(1)

        hx.reset()

    if DEBUG_LOG:
        print("init_scales HX objects reset at {:.3f} secs.".format(time.process_time() - t_start))

    return hx_list

# Read the TARE_FILENAME defined in CONFIG, return the contained json as a python dictionary
def read_tare_file():
    # if there is an existing tare file, previous values will be read from that
    if DEBUG_LOG:
        print("reading tare file {}".format(CONFIG["TARE_FILENAME"]))

    try:
        tare_file_handle = open(CONFIG["TARE_FILENAME"], "r")
        file_text = tare_file_handle.read()
        tare_dictionary = json.loads(file_text)
        tare_file_handle.close()
        print("LOADED TARE FILE {}".format(CONFIG["TARE_FILENAME"]))
        return tare_dictionary
    except Exception as e:
        print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(CONFIG["TARE_FILENAME"]))
        print(e)

    return {}

# Write the tare_list and current timestamp as json into the file TARE_FILENAME defined in CONFIG
def write_tare_file(tare_list):
    acp_ts = time.time() # epoch time in floating point seconds

    tare_json = """
       {{ "acp_ts": {:.3f},
          "tares": [ {:.1f}, {:.1f}, {:.1f}, {:1f} ]
       }}
       """.format(acp_ts, *tare_list)

    try:
        tare_file_handle = open(CONFIG["TARE_FILENAME"], "w")
        tare_file_handle.write(tare_json)
        tare_file_handle.close()
    except:
        print("tare scales file write to tare json file {}".format(CONFIG["TARE_FILENAME"]))

# Return True if the latest tare readings are within the bounds set in CONFIG.
# This is designed to ensure we don't 'tare' with the pot sitting on the sensor.
def tare_ok(tare_list):
    i = 0
    # We compare each value in the tare_list and see if it is within the allowed TARE_WIDTH
    # of the corresponding approximate expected reading in TARE_READINGS. Also the total
    # of the readings must be within the config total +/- * TARE_WIDTH * 2.
    # We will only return True if *all* tare readings and the tare_total are within acceptable bounds.
    tare_delta_total = 0
    max_delta = 0 # we track max delta for debug purposes
    max_i = 0
    while i < len(tare_list):
        tare_delta = abs(tare_list[i] - CONFIG["TARE_READINGS"][i])
        if tare_delta > max_delta:
            max_delta = tare_delta
            max_i = i
        tare_delta_total += tare_delta
        if tare_delta > CONFIG["TARE_WIDTH"]:
            if DEBUG_LOG:
                print("tare_ok reading[{}] {:.0f} out of range vs {:.0f} +/- {}".format(i,
                    tare_list[i],
                    CONFIG["TARE_READINGS"][i],
                    CONFIG["TARE_WIDTH"]))

            return False
        else:
            i += 1

    if tare_delta_total > CONFIG["TARE_WIDTH"] * 2:
        if DEBUG_LOG:
            print("tare_ok total delta {} of [{}] is out of range for [{}] +/- (2*){}".format(tare_delta_total,
                u.list_to_string(tare_list,"{:+.0f}"),
                u.list_to_string(CONFIG["TARE_READINGS"],"{:+.0f}"),
                CONFIG["TARE_WIDTH"]))

        return False

    if DEBUG_LOG:
        print("tare_ok is OK, max delta[{}] was {:.0f}".format(max_i, max_delta))

    return True

# Find the 'tare' for load cell 1 & 2
def tare_scales(hx_list):

    t_start = time.process_time()

    tare_list = []

    # we 'tare' each sensor, this will also update the tare value used in each HX771 object
    for hx in hx_list:
        # Here we initialize the 'empty weight' settings
        tare_list.append( hx.tare_A() )

    if DEBUG_LOG:
        print("tare_scales readings [ {} ] completed at {:.3f} secs.".format( u.list_to_string(tare_list, "{:+.0f}"),
                                                                              time.process_time() - t_start))

    # If the tare_list is 'ok' (i.e. within bounds) we will write it to the tare file and return it as the result
    if tare_ok(tare_list):
        write_tare_file(tare_list)
        return tare_list

    # Otherwise.. the tare reading was NOT ok...
    # The new tare readings are out of range, so use persisted values
    tare_dictionary = read_tare_file()

    tare_list = tare_dictionary["tares"]

    # As the measured tare values are not acceptable, we now update the HX711 objects with the persisted values.
    i = 0
    for hx in hx_list:
        hx.set_offset_A(tare_list[i])
        i += 1

    if DEBUG_LOG:
        output_string = "tare_scales readings out of range, using persisted values [ {} ]"
        print(output_string.format(u.list_to_string(tare_list,"{:+.0f}")))

    return tare_list

# Return the weight in grams, combined from both load cells
def get_weight():
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

    if DEBUG_LOG:
        output_string = "get_weight readings [ {} ] completed at {:.3f} secs."
        print( output_string.format(u.list_to_string(debug_list, "{:+.0f}"), time.process_time() - t_start))

    return total_reading / CONFIG["WEIGHT_FACTOR"] # grams


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# LCD code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def init_lcd():
    t_start = time.process_time()

    LCD = ST7735()

    LCD.begin()

    image = Image.open('pot.bmp')
    #LCD.LCD_PageImage(image)
    LCD.display(image)

    if DEBUG_LOG:
        print("init_lcd in {:.3f} sec.".format(time.process_time() - t_start))

    return LCD

# Update a PIL image with the weight, and send to LCD
# Note we are creating an image smaller than the screen size, and only updating a part of the display
def update_lcd(weight_g):
    global LCD

    t_start = time.process_time()

    # create a blank image to write the weight on
    image = Image.new( "RGB",
                       ( CONFIG["WEIGHT_WIDTH"],
                         CONFIG["WEIGHT_HEIGHT"]),
                       CONFIG["WEIGHT_COLOR_BG"])
    draw = ImageDraw.Draw(image)

    # convert weight to string with fixed 5 digits including 1 decimal place, max 9999.9

    display_number = weight_g

    if display_number >= 10000:
        display_number = 9999.9

    draw_string = "{:5.1f}".format(display_number) # 10 points for witty variable name

    # calculate x coordinate necessary to right-justify text
    string_width, string_height = draw.textsize(draw_string, font=FONT)

    # embed this number into the blank image we created earlier
    draw.text((CONFIG["WEIGHT_WIDTH"]-string_width-CONFIG["WEIGHT_RIGHT_MARGIN"],0),
              draw_string,
              fill = CONFIG["WEIGHT_COLOR_FG"],
              font=FONT)

    # display image on screen at coords x,y. (0,0)=top left.
    LCD.display_window(image,
                      CONFIG["WEIGHT_X"],
                      CONFIG["WEIGHT_Y"],
                      CONFIG["WEIGHT_WIDTH"],
                      CONFIG["WEIGHT_HEIGHT"])

    # display a two-line debug display of the weights from both load cells
    if DEBUG_LOG:
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

    if DEBUG_LOG:
        print("LCD updated with weight {:.1f} in {:.3f} secs.".format(display_number, time.process_time() - t_start))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# SEND DATA TO PLATFORM
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def send_data(post_data):
    try:
        print("send_data() to {}".format(CONFIG["FEEDMAKER_URL"]))
        response = requests.post(
                  CONFIG["FEEDMAKER_URL"],
                  headers={ CONFIG["FEEDMAKER_HEADER_KEY"] : CONFIG["FEEDMAKER_HEADER_VALUE"] },
                  json=post_data
                  )

        print("status code",response.status_code)
    except Exception as e:
        print("send_data() error with {}".format(post_data))
        print(e)

def send_weight(weight_g):
    now = time.time()
    post_data = {  'msg_type': 'coffee_pot_weight',
                   'request_data': [ { 'acp_id': CONFIG["SENSOR_ID"],
                                       'acp_type': CONFIG["SENSOR_TYPE"],
                                       'acp_ts': now,
                                       'weight': weight_g,
                                       'acp_units': 'GRAMS'
                                    }
                                   ]
            }
    send_data(post_data)

def send_event(event_code):
    now = time.time()
    post_data = {  'msg_type': 'coffee_pot_event',
                   'request_data': [ { 'acp_id': CONFIG["SENSOR_ID"],
                                       'acp_type': CONFIG["SENSOR_TYPE"],
                                       'acp_ts': now,
                                       'event_code': event_code
                                     }
                                   ]
            }
    send_data(post_data)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Event pattern recognition
# In general these routines look at the sample_history buffer and
# decide if an event has just become recognizable, e.g. POT_NEW
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

# store the current weight in the sample_history circular buffer
def record_sample(weight_g):
    global sample_history
    global sample_history_index

    sample_history[sample_history_index] = { 'ts': time.time(), 'weight': weight_g }
    sample_history_index = (sample_history_index + 1) % SAMPLE_HISTORY_SIZE

# Lookup the weight in the sample_history buffer at offset before now
# This returns None or an object { 'ts': <timestamp>, 'weight': <grams> }
def lookup_sample(offset):
    global sample_history
    global sample_history_index
    if offset >= SAMPLE_HISTORY_SIZE:
        return None
    index = (sample_history_index + SAMPLE_HISTORY_SIZE - i) % SAMPLE_HISTORY_SIZE
    return sample_history(index)

# Calculate the average weight recorded over the previous 'duration' seconds from offset.
# Returns a tuple of <average weight>, <index> where <index> is the sample_history offset
# one sample earlier than the offset & duration selected.
# E.g. weight_average(0,3) will find the average weight of the most recent 3 seconds.
def weight_average(offset, duration):
    # lookup the first weight to get that weight (grams) and timestamp
    sample = lookup_sample(offset)
    if sample == None:
        return None
    index = offset
    total_weight = sample["weight"]
    end_time = sample["ts"] - duration
    sample_count = 1
    while True: # Repeat .. Until
        # select previous index in circular buffer
        index = (index + SAMPLE_HISTORY_SIZE - 1) % SAMPLE_HISTORY_SIZE
        if index == offset:
            # we've exhausted the full buffer
            return None
        sample = lookup_sample(index)
        if sample == None
            # we've exhausted the values in the partially filled buffer
            return None
        if sample["ts"] < end_time:
            break
        total_weight += sample["weight"]
        sample_count += 1

    return total_weight / sample_count, index

# Look in the sample_history buffer (including latest) and try and spot a new event.
# Uses the event_history buffer to avoid repeated messages for the same event
def test_event():
    return


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# init() called on startup
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def init():
    global LCD
    global hx_list

    # read the sensor_config.json file for updated config values
    load_config()

    # initialize the st7735 for LCD display
    LCD = init_lcd()

    # initialize the two hx711 A/D converters
    hx_list = init_scales()

    # find the scales 'zero' reading
    tare_scales(hx_list)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# loop() - main execution loop
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def loop():
    prev_time = time.time() # floating point seconds in epoch

    while True:
        try:
            t_start = time.process_time()

            #----------------
            # GET WEIGHT
            # ---------------

            # get readings from A and B channels
            weight_g = get_weight()

            if DEBUG_LOG:
                print("loop got weight {:.1f} at {:.3f} secs.".format(weight_g, time.process_time() - t_start))

            # store weight and time in sample_history
            record_sample(weight_g)

            #----------------
            # UPDATE LCD
            # ---------------

            update_lcd(weight_g)

            if DEBUG_LOG:
                print("loop update_lcd {:.1f} at {:.3f} secs.".format(weight_g, time.process_time() - t_start))

            #----------------------
            # SEND DATA TO PLATFORM
            # ---------------------

            now = time.time() # floating point time in seconds since epoch
            if now - prev_time > 30:
                print ("SENDING WEIGHT {:5.1f}, {}".format(weight_g, time.ctime(now)))

                send_weight(weight_g)

                prev_time = now

                if DEBUG_LOG:
                    print("loop send data at {:.3f} secs.".format(time.process_time() - t_start))
                    for i in range(30):
                        sample = lookup_sample(i)
                        print("sample", sample["ts"], sample["weight"])
                    a = weight_average(0,2)
                    print("sample 2s average", a)

            elif DEBUG_LOG:
                print ("WEIGHT {:5.1f}, {}".format(weight_g, time.ctime(now)))

            #hx.power_down()
            #hx.power_up()

            if DEBUG_LOG:
                print("loop time (before sleep) {:.3f} secs.\n".format(time.process_time() - t_start))

            time.sleep(1.0)

        except (KeyboardInterrupt, SystemExit):
            return 0  # return exit code on interruption

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# finish() - cleanup and exit if main loop is interrupted
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

def finish():
    print("\n")

    print("GPIO cleanup()...")

    GPIO.cleanup()

    print("Exitting")

    sys.exit()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

# declare globals
LCD = None # ST7735 LCD display chip
hx_list = None # LIST of hx711 A/D chips

EVENT_HISTORY_SIZE = 5 # keep track of the most recent 5 events sent to server
event_history = [ None ] * EVENT_HISTORY_SIZE

# Note sample_history is a *circular* buffer (for efficiency)
SAMPLE_HISTORY_SIZE = 100 # store weight samples 0..99
weight_index = 0
sample_history = [ None ] * SAMPLE_HISTORY_SIZE # buffer for 100 weight samples ~= 10 seconds

debug_list = [ 1, 2, 3, 4] # weights from each load cell, for debug display on LCD

# Initialize everything
init()

# Infinite loop until killed, reading weight and sending data
interrupt_code = loop()

# Cleanup and quit
finish()

