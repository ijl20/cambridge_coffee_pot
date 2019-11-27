# Emulates st7735_ijl20 library

# Raspberry Pi LCD support via ST7735 control chip

import time
import numbers
import time
import numpy as np
import math
import pygame as pg

from PIL import Image
from PIL import ImageDraw

from st7735_ijl20.chart import Chart

LCD_WIDTH = 160
LCD_HEIGHT = 128

# Pin definition
LCD_RST_PIN         = 27
LCD_DC_PIN          = 25
LCD_CS_PIN          = 8
LCD_BL_PIN          = 24

LCD_X = 2
LCD_Y = 1
LCD_X_MAXPIXEL = 132  #LCD width maximum memory
LCD_Y_MAXPIXEL = 162  #LCD height maximum memory

SCREEN_WHITE = (255,255,255)
SCREEN_BLACK = (0,0,0)

class ST7735_EMULATOR(object):
    """Representation of an ST7735 TFT LCD."""

    def __init__(self,
                 dc=LCD_DC_PIN,
                 rst=LCD_RST_PIN,
                 cs=LCD_CS_PIN,
                 bl=LCD_BL_PIN,
                 width=LCD_WIDTH,
                 height=LCD_HEIGHT,
                 scale=2):
        """
        This emulator is suitable for display updates using the same methods as st7735_ijl20.st7735

        The 'register' initializations (self.setup(), self.set_scan(), self.begin()) are simple 'pass' functions as
        for this emulator all the setup necessary can be implemented in the class __init__.

        An effort has been made to keep most of the update code the same as in the st7735_ijl20.st7735 i.e.
        using RGB565 pixels and doing all updates via data bytes sent serially to a defined 'window' on the lcd.
        """

        print("initializing LCD_ST7735 EMULATOR")

        # Dimensions of emulated LCD (self.lcd)
        self.width = width
        self.height = height

        # Dimensions of display window (self.screen)
        self.screen_width = width * scale
        self.screen_height = height * scale

        self.set_window(0,0,self.width,self.height)

        # Create pygame display window
        # self.screen is the actual display window used to show the LCD
        # which may be scaled from the emulated LCD
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))

        pg.display.set_caption('ST7735')

        # Create pygame surface we draw on
        # self.lcd is the emulated st7735 display (i.e. 160 x 128)
        self.lcd = pg.Surface((self.width, self.height))

        self.lcd.fill(SCREEN_WHITE, ((0,0),(self.width,self.height)))

        self.screen_update()

    def screen_update(self):
        self.screen.blit(pg.transform.scale(self.lcd,(self.screen_width, self.screen_height)),[0,0])
        pg.display.update()

   # numpy is fastest way to convert image to bytes
    def image_to_data(self, image):
        """Generator function to convert a PIL image to 16-bit 565 RGB bytes."""
        # NumPy is much faster at doing this. NumPy code provided by:
        # Keith (https://www.blogger.com/profile/02555547344016007163)
        pb = np.array(image.convert('RGB')).astype('uint16')
        color = ((pb[:,:,0] & 0xF8) << 8) | ((pb[:,:,1] & 0xFC) << 3) | (pb[:,:,2] >> 3)
        return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()

    # Convert [ 0xab, 0xcd ]
    def pixel565_to_rgb(self, byte_list):
        R = ( byte_list[0] & 0xF8 ) >> 3
        G = ( byte_list[0] & 0x07 ) << 3 | ( byte_list[1] >> 5 )
        B = ( byte_list[1] & 0x1F )
        return ( math.floor( R / 31 * 255), math.floor(G / 63 * 255), math.floor(B / 31 * 255))

    def send_data(self, data):
        """Write a byte or array of bytes to the display as display data."""
        x = self.window_x
        y = self.window_y
        w = self.window_w
        h = self.window_h

        pixel = [] # will accumulate bytes for pixel
        pixel_len = 2

        for v in data:
            pixel.append(v)
            if len(pixel) == pixel_len:
                color = self.pixel565_to_rgb(pixel)
                pixel = []
                self.lcd.set_at((x,y), color)
                x = x + 1
                if x >= self.window_x + self.window_w:
                    x = self.window_x
                    y = y + 1
                    if y >= self.window_y + self.window_h:
                        y = self.window_y

        self.screen_update()

    """    Common register initialization    """
    def setup(self):
        pass

    #********************************************************************************
    #function:  Set the display scan and color transfer modes
    #********************************************************************************
    def set_scan(self):
        pass

    #/********************************************************************************
    #function:  send_color_pixels
    #parameter:
    #       color  :   565 RGB 16-bit value
    #********************************************************************************/
    def send_color_pixels(self, color , width,  height):
        pixelbytes = [ (color >> 8) & 0xFF, (color & 0xFF) ] * (width * height)
        self.send_data(pixelbytes)

    #/********************************************************************************
    #function:  set_pixel_color
    #parameter:
    #       x :   The x coordinate of the point
    #       y :   The y coordinate of the point
    #       color  :   565 RGB 16-bit value
    #********************************************************************************/
    def set_pixel_color(self,  x,  y, color ):
        if ( ( x <= self.width ) and ( y <= self.height ) ):
            self.set_window(x, y, 1, 1)
            self.send_color_pixels( color , 1 , 1)

    #/********************************************************************************
    #function:  Fill the area with the color
    #parameter:
    #       Xstart :   Start point x coordinate
    #       Ystart :   Start point y coordinate
    #       Xend   :   End point coordinates
    #       Yend   :   End point coordinates
    #       color  :   565 RGB 16-bit value
    #********************************************************************************/
    def set_rectangle_color(self, x, y, w, h, color):
        Xend = x + w
        Yend = y + h
        self.set_window( x, y, w, h )
        self.send_color_pixels( color, w ,h )

    #/********************************************************************************
    #function:
    #           Clear screen
    #********************************************************************************/
    def clear(self):
        self.set_rectangle_color(0,0, LCD_X_MAXPIXEL , LCD_Y_MAXPIXEL  , color = 0xFFFF)#white

    #/********************************************************************************
    #function:
    #           initialization
    #********************************************************************************/
    def begin(self): # was LCD_Init
        self.clear()

    #/********************************************************************************
    #function:  Sets the start position and size of the display area
    #parameter:
    #   x,y  :   coordinates of top-left corner of area
    #   w,h  :   width, height of area
    #********************************************************************************/
    def set_window(self, x, y, w, h ): # was LCD_SetWindows
        self.window_x = x
        self.window_y = y
        self.window_w = w
        self.window_h = h

    # -------------------------------------
    # ----- RESET THE LCD DISPLAY  --------
    # -------------------------------------
    def reset(self):
        self.clear()
    # -------------------------------------
    # ----- CLEANUP AT END OF USE  --------
    # -------------------------------------
    def cleanup(self):
        print("ST7735 Emulator cleanup()")

    # -----------------------------------------------------------------------
    # Display a full-screen image
    # -----------------------------------------------------------------------
    def display(self, image=None):
        """Write the provided image to the hardware, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # Set address bounds to entire display.
        self.set_window( 0, 0, self.width, self.height )
        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(self.image_to_data(image))
        # Write data to hardware.
        self.send_data(pixelbytes)

    # -----------------------------------------------------------------------
    # display an image within a window on the screen
    # -----------------------------------------------------------------------
    def display_window(self, image, x, y, w, h):
        """Write the provided image to the hardware, it should be RGB format and
         w pixels x h pixels
        """
        # Set address bounds to entire display.
        self.set_window( x, y, w, h)
        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(self.image_to_data(image))
        # Write data to hardware.
        self.send_data(pixelbytes)

    # -----------------------------------------------------------------------
    # Add a scrolling chart to the display
    # -----------------------------------------------------------------------

    # Initialize a 'Chart' object, and return object when created.
    def add_chart(self, config=None):
        global DEFAULT_CHART

        # Note this ST7735 object (self) is passed to the Chart() as a parameter.
        chart = Chart(self, config)

        chart.clear()
        return chart

