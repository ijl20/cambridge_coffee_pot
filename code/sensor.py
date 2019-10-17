#! /usr/bin/python3

# info sent in json packet to feed handler
SENSOR_ID = 'cambridge_coffee_pot'
SENSOR_TYPE = 'coffee_pot'
ACP_TOKEN = 'testtoken'

# linear calibration of A and B channels of scale
A_SCALE = 488.1 # grams per reading value
B_SCALE = 112.4

# Python libs
import time
import sys
import RPi.GPIO as GPIO
import simplejson as json
import requests

# D to A converter libs
sys.path.append('hx711')
from hx711 import HX711

# LCD display libs
sys.path.append('LCD_1in8') # LCD display (160x128 color 1.8")
import LCD_1in8
import LCD_Config

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

# LCD panel size in pixels (0,0) is top left
DISPLAY_WIDTH = 160                # LCD panel width in pixels
DISPLAY_HEIGHT = 128               # LCD panel height

# Pixel size and coordinates of the 'Weight' display
DISPLAY_WEIGHT_HEIGHT = 40
DISPLAY_WEIGHT_WIDTH = 160
DISPLAY_WEIGHT_COLOR_FG = "WHITE"
DISPLAY_WEIGHT_COLOR_BG = "BLACK"
DISPLAY_WEIGHT_X = 0
DISPLAY_WEIGHT_Y = 60
DISPLAY_WEIGHT_RIGHT_MARGIN = 10


FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 40)

def init_lcd():
    print ("**********Init LCD**********")

    LCD = LCD_1in8.LCD()

    Lcd_ScanDir = LCD_1in8.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
    LCD.LCD_Init(Lcd_ScanDir)

    image = Image.open('pot.bmp')
    LCD.LCD_PageImage(image)

    return LCD

# Initialize scales, return hx711 object
def init_scales():
    hx = HX711(5, 6)

    # set_reading_format(order bytes to build the "long" value, order of the bits inside each byte) MSB | LSB
    # According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx.set_reading_format("MSB", "MSB")

    hx.set_reference_unit_A(488.1)
    hx.set_reference_unit_B(112.4)

    hx.reset()

    # to use both channels, you'll need to tare them both
    hx.tare_A()
    hx.tare_B()
    print("Tare A&B done! Add weight now...")

    return hx

# Return the weight in grams
def get_weight():
    global hx

    val_A = hx.get_weight_A(1)
    val_B = hx.get_weight_B(1)
    return val_A + val_B # grams

# Update a PIL image with the weight, and send to LCD
# Note we are creating an image smaller than the screen size, and only updating a part of the display
def update_lcd(weight_g):
    global LCD

    image = Image.new("RGB", (DISPLAY_WEIGHT_WIDTH, DISPLAY_WEIGHT_HEIGHT), DISPLAY_WEIGHT_COLOR_BG)
    draw = ImageDraw.Draw(image)
    # convert weight to fixed 5 digits including 1 decimal place
    if weight_g >= 10000:
        weight_g = 9999.9

    draw_string = "{:5.1f}".format(weight_g) # 10 points for witty variable name
    # calculate x coordinate necessary to right-justify text
    string_width, string_height = draw.textsize(draw_string, font=FONT)
    draw.text((DISPLAY_WEIGHT_WIDTH-string_width-DISPLAY_WEIGHT_RIGHT_MARGIN,0), draw_string, fill = DISPLAY_WEIGHT_COLOR_FG, font=FONT)

    LCD.LCD_ShowImage(image, DISPLAY_WEIGHT_X, DISPLAY_WEIGHT_Y, DISPLAY_WEIGHT_WIDTH, DISPLAY_WEIGHT_HEIGHT)

def cleanAndExit():
    print("Cleaning...")

    GPIO.cleanup()

    print("Bye!")
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
    LCD = init_lcd()
    hx = init_scales()

def loop():
    prev_time = time.time() # floating point seconds in epoch

    while True:
        try:
            # get readings from A and B channels
            weight_g = get_weight()

            update_lcd(weight_g)

            now = time.time() # floating point time in seconds since epoch
            if now - prev_time > 30:
                print ("SENDING {:5.1f}, {}".format(weight_g, time.ctime(now)))
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
            else:
                print ("WEIGHT {:5.1f}, {}".format(weight_g, time.ctime(now)))

            #hx.power_down()
            #hx.power_up()
            time.sleep(1.0)

        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()

# globals
LCD = None
hx = None

init()

loop()


