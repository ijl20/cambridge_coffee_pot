#! /usr/bin/python3

# for dev / debug
DEBUG_LOG = True

# info sent in json packet to feed handler
SENSOR_ID = 'cambridge_coffee_pot'
SENSOR_TYPE = 'coffee_pot'
ACP_TOKEN = 'testtoken'
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

FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 40)
DEBUG_FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 14)

# Load sensor configuration from Json config file
def load_config():
    filename = CONFIG_FILENAME
    try:
        if len(sys.argv) > 1 and sys.argv[1]:
            filename = sys.argv[1]

        if DEBUG_LOG:
            print("Config file is {}".format(filename))

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
        print("LOADED CONFIG FILE {} {}".format(filename, CONFIG["WEIGHT_COLOR_BG"]))
    except Exception as e:
        print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(filename))
        print(e)


def init_lcd():
    t_start = time.process_time()

    LCD = ST7735()

    #Lcd_ScanDir = LCD_1in8.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
    #LCD.LCD_Init(Lcd_ScanDir)

    LCD.begin()

    image = Image.open('pot.bmp')
    #LCD.LCD_PageImage(image)
    LCD.display(image)

    if DEBUG_LOG:
        print("init_lcd in {:.3f} sec.".format(time.process_time() - t_start))

    return LCD

# Initialize scales, return hx711 objects
# Note there are TWO load cells, each with their own HX711 A/D converter.
# Each HX711 has an A and a B channel, we are only using the A channel of each.
def init_scales():

    t_start = time.process_time()

    hx_1 = HX711(5, 6) # first hx711, connected to load cell 1
    hx_1.DEBUG_LOG = DEBUG_LOG

    hx_2 = HX711(12, 13) # second hx711, connected to load cell 2
    hx_2.DEBUG_LOG = DEBUG_LOG

    if DEBUG_LOG:
        print("init_scales HX objects created at {:.3f} secs.".format(time.process_time() - t_start))

    # set_reading_format(order bytes to build the "long" value, order of the bits inside each byte) MSB | LSB
    # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx_1.set_reading_format("MSB", "MSB")
    hx_2.set_reading_format("MSB", "MSB")

    hx_1.set_reference_unit_A(1)
    hx_2.set_reference_unit_A(1)

    hx_1.reset()
    hx_2.reset()

    if DEBUG_LOG:
        print("init_scales HX objects reset at {:.3f} secs.".format(time.process_time() - t_start))

    return [ hx_1, hx_2 ]

# Find the 'tare' for load cell 1 & 2
def tare_scales(hx):

    # if there is an existing tare file, previous values will be read from that
    if DEBUG_LOG:
        print("reading tare file {}".format(CONFIG["TARE_FILENAME"]))

    try:
        tare_file_handle = open(CONFIG["TARE_FILENAME"], "r")
        file_text = tare_file_handle.read()
        tare_dictionary = json.loads(file_text)
        tare_file_handle.close()
        print("LOADED TARE FILE {}".format(CONFIG["TARE_FILENAME"]))
    except Exception as e:
        print("READ CONFIG FILE ERROR. Can't read supplied filename {}".format(CONFIG["TARE_FILENAME"]))
        print(e)

    t_start = time.process_time()

    # Here we initialize the 'empty weight' settings
    tare_1 = hx[0].tare_A()

    if DEBUG_LOG:
        print("tare_scales tare 1 {:.1f} completed at {:.3f} secs.".format(tare_1, time.process_time() - t_start))

    tare_2 = hx[1].tare_A()

    if DEBUG_LOG:
        print("tare_scales tare 2 {:.1f} completed at {:.3f} secs.".format(tare_2, time.process_time() - t_start))

    acp_ts = time.time() # epoch time in floating point seconds

    tare_json = """
       {{ "acp_ts": {:.3f},
          "tares": [ {:.1f}, {:.1f} ]
       }}
       """.format(acp_ts, tare_1, tare_2)

    try:
        tare_file_handle = open(CONFIG["TARE_FILENAME"], "w")
        tare_file_handle.write(tare_json)
        tare_file_handle.close()
    except:
        print("tare scales filed write to tare json file {}".format(CONFIG["TARE_FILENAME"]))

    return [ tare_1, tare_2 ]

# Return the weight in grams, combined from both load cells
def get_weight():
    global hx # hx is [ hx_1, hx_2 ]
    global debug1, debug2

    t_start = time.process_time()

    # get_weight accepts a parameter 'number of times to sample weight and then average'
    reading_1 = hx[0].get_weight_A(1)
    debug1 = reading_1 # store weight for debug display

    if DEBUG_LOG:
        print("get_weight reading_1 {:5.1f} completed at {:.3f} secs.".format(reading_1, time.process_time() - t_start))

    reading_2 = hx[1].get_weight_A(1)
    debug2 = reading_2 # store weight for debug display

    if DEBUG_LOG:
        print("get_weight reading_2 {:5.1f} completed at {:.3f} secs.".format(reading_2, time.process_time() - t_start))

    return (reading_1  + reading_2) / CONFIG["WEIGHT_FACTOR"] # grams

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
        image = Image.new("RGB", (50, 40), "BLACK")
        draw = ImageDraw.Draw(image)
        draw_string = "{:5.1f}".format(debug1)
        draw.text((0,0), draw_string, fill="YELLOW", font=DEBUG_FONT)
        draw_string = "{:5.1f}".format(debug2)
        draw.text((0,20), draw_string, fill="YELLOW", font=DEBUG_FONT)
        LCD.display_window(image, 110, 5, 50, 40)

    if DEBUG_LOG:
        print("LCD updated with weight {:.1f} in {:.3f} secs.".format(display_number, time.process_time() - t_start))

def cleanAndExit():
    print(" GPIO cleanup()...")

    GPIO.cleanup()

    sys.exit()

def send_data(post_data, token):
    response = requests.post('https://tfc-app2.cl.cam.ac.uk/test/feedmaker/test/general',
              headers={'X-Auth-Token': token },
              json=post_data
              )

    print("status code",response.status_code)

def init():
    global LCD
    global hx

    # read the sensor_config.json file for updated config values
    load_config()

    # initialize the st7735 for LCD display
    LCD = init_lcd()

    # initialize the two hx711 A/D converters
    hx = init_scales()

    # find the scales 'zero' reading
    tare_scales(hx)

def loop():
    prev_time = time.time() # floating point seconds in epoch

    while True:
        try:
            t_start = time.process_time()
            # get readings from A and B channels
            weight_g = get_weight()

            if DEBUG_LOG:
                print("loop got weight {:.1f} at {:.3f} secs.".format(weight_g, time.process_time() - t_start))

            update_lcd(weight_g)

            if DEBUG_LOG:
                print("loop update_lcd {:.1f} at {:.3f} secs.".format(weight_g, time.process_time() - t_start))

            now = time.time() # floating point time in seconds since epoch
            if now - prev_time > 30:
                print ("SENDING WEIGHT {:5.1f}, {}".format(weight_g, time.ctime(now)))
                post_data = { 'request_data': [ { 'acp_id': SENSOR_ID,
                                                  'acp_type': SENSOR_TYPE,
                                                  'acp_ts': now,
                                                  'weight': weight_g,
                                                  'acp_units': 'GRAMS'
                                                 }
                                              ]
                            }
                send_data(post_data, ACP_TOKEN)
                prev_time = now

                if DEBUG_LOG:
                    print("loop send data at {:.3f} secs.".format(time.process_time() - t_start))

            elif DEBUG_LOG:
                print ("WEIGHT {:5.1f}, {}".format(weight_g, time.ctime(now)))

            #hx.power_down()
            #hx.power_up()

            if DEBUG_LOG:
                print("loop time (before sleep) {:.3f} secs.".format(time.process_time() - t_start))

            time.sleep(1.0)

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

# globals
LCD = None # ST7735 LCD display chip
hx = None # LIST of hx711 A/D chips

debug1 = 0.0 # weights from each load cell, for debug
debug2 = 0.0

# Initialize everything
init()

# Infinite loop until killed, reading weight and sending data
loop()

#update_lcd(1122.3)
#time.sleep(2.0)
#cleanAndExit()

