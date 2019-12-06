    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # Display code
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------

import time
import math

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 30)
DEBUG_FONT = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 14)

# ST7735 color mappings
str_to_color = { "YELLOW": 0xFFE0,    # yellow 565 RGB
                 "BLUE": 0x001F    # blue 565 RGB
               }

class Display(object):

    def __init__(self, settings=None, emulate=False):

        if emulate:
            from st7735_ijl20.st7735_emulator import ST7735_EMULATOR as ST7735
        else:
            from st7735_ijl20.st7735 import ST7735

        self.settings = settings

        t_start = time.process_time()

        self.prev_lcd_time = None

        self.LCD = ST7735()

        self.LCD.begin()

        image = Image.open('pot.bmp')
        #LCD.LCD_PageImage(image)
        self.LCD.display(image)

        print("init_lcd in {:.3f} sec.".format(time.process_time() - t_start))

    # ------------------
    # Initial display
    # ------------------
    def begin(self):
        self.chart = self.LCD.add_chart()

    # -------------------------------------------------------------------
    # ------ DRAW NUMERIC VALUE ON LCD  ---------------------------------
    # -------------------------------------------------------------------
    def draw_value(self, value):
        # create a blank image to write the weight on
        image = Image.new( "RGB",
                           ( self.settings["VALUE_WIDTH"],
                             self.settings["VALUE_HEIGHT"]),
                           self.settings["VALUE_COLOR_BG"])

        draw = ImageDraw.Draw(image)

        # convert weight to string with fixed 5 digits including 1 decimal place, max 9999.9

        display_number = value

        if display_number >= 10000:
            display_number = 9999.9

        draw_string = "{:5.0f}".format(display_number) # 10 points for witty variable name

        # calculate x coordinate necessary to right-justify text
        string_width, string_height = draw.textsize(draw_string, font=FONT)

        # embed this number into the blank image we created earlier
        draw.text((self.settings["VALUE_WIDTH"]-string_width-self.settings["VALUE_RIGHT_MARGIN"],0),
                draw_string,
                fill = self.settings["VALUE_COLOR_FG"],
                font=FONT)

        # display image on screen at coords x,y. (0,0)=top left.
        self.LCD.display_window(image,
                        self.settings["VALUE_X"],
                        self.settings["VALUE_Y"],
                        self.settings["VALUE_WIDTH"],
                        self.settings["VALUE_HEIGHT"])

    # -------------------------------------------------------------------
    # ------ DRAW DEBUG READINGS ON LCD       ---------------------------
    # -------------------------------------------------------------------
    def draw_debug(self, debug_list):
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

            self.LCD.display_window(image, 0, 40, 160, 40)

    # Update a PIL image with the weight, and send to LCD
    # Note we are creating an image smaller than the screen size, and only updating a part of the display
    def update(self, ts, sample_buffer, debug_list):

        t_start = time.process_time()

        if (self.prev_lcd_time is None) or (ts - self.prev_lcd_time > 1):
            sample_value, offset, duration, sample_count = sample_buffer.median(0,1) # get median weight value for 1 second
            if not sample_value == None:
                self.draw_value(sample_value)

            self.prev_lcd_time = ts

            if self.settings["LOG_LEVEL"] == 1:
                if sample_value == None:
                    print("loop update_lcd skipped (None) at {:.3f} secs.".format(time.process_time() - t_start))
                else:
                    print("loop update_lcd {:.1f} at {:.3f} secs.".format(sample_value, time.process_time() - t_start))

            # draw_debug() is disabled
            #self.draw_debug(debug_list)

        # -------------------------------------------------------------------
        # ------ ADD CURRENT WEIGHT TO BAR CHART   --------------------------
        # -------------------------------------------------------------------

        latest_sample = sample_buffer.get(0)
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

    def finish(self):
        self.LCD.cleanup()

# Pot fullness display object
class Pot(object):

    def __init__(self, LCD=None, x=0, y=0, w=40, h=128, settings=None):
        self.LCD = LCD

        # set pot coordinates on display
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # Set fg and bg colors
        if settings is None or not "POT_FG" in settings:
            self.FG_COLOR =str_to_color["YELLOW"]
        else:
            self.FG_COLOR = str_to_color[settings["POT_FG"]]

        if settings is None or not "POT_BG" in settings:
            self.BG_COLOR = str_to_color["BLUE"]
        else:
            self.BG_COLOR = str_to_color[settings["POT_BG"]]


    def begin(self):

        self.LCD.set_rectangle_color(self.x, self.y, self.w, self.h, self.BG_COLOR)

        self.prev_y = self.y + self.h 


    # convert a 'full' ratio 0..1 to a y pixel offset from top of screen.
    def ratio_to_y(self, ratio):

        # ratio is 0..1
        return math.floor(self.y + self.h * (1 - ratio))

    # Update the displayed vertical bar
    def update(self, ratio):

        new_y = self.ratio_to_y(ratio)

        if new_y < self.prev_y:
            # new ratio was higher
            # add foreground pixels
            h = self.prev_y - new_y
            self.LCD.set_rectangle_color(self.x, new_y, self.w, h, self.FG_COLOR)
        elif new_y > self.prev_y:
            # new ratio was lower
            # reduce bar by adding background pixels
            h = new_y - self.prev_y
            self.LCD.set_rectangle_color(self.x, self.prev_y, self.w, h, self.BG_COLOR)

        self.prev_y = new_y

        


