# Raspberry Pi LCD support via ST7735 control chip

import RPi.GPIO as GPIO
import spidev
import time
import numbers
import time
import numpy as np

from PIL import Image
from PIL import ImageDraw

SPI_CLOCK_HZ = 9000000 # 9 MHz

# ------------------------------------------
# ST7735 display controller chip command set
# ------------------------------------------

# Constants for interacting with display registers.
ST7735_NOP         = 0x00
ST7735_SWRESET     = 0x01
ST7735_RDDID       = 0x04
ST7735_RDDST       = 0x09

ST7735_SLPIN       = 0x10
ST7735_SLPOUT      = 0x11
ST7735_PTLON       = 0x12
ST7735_NORON       = 0x13

# ILI9341_RDMODE      = 0x0A
# ILI9341_RDMADCTL    = 0x0B
# ILI9341_RDPIXFMT    = 0x0C
# ILI9341_RDIMGFMT    = 0x0A
# ILI9341_RDSELFDIAG  = 0x0F

ST7735_INVOFF      = 0x20
ST7735_INVON       = 0x21
# ILI9341_GAMMASET    = 0x26
ST7735_DISPOFF     = 0x28
ST7735_DISPON      = 0x29

ST7735_CASET       = 0x2A
ST7735_RASET       = 0x2B
ST7735_RAMWR       = 0x2C
ST7735_RAMRD       = 0x2E

ST7735_PTLAR       = 0x30
ST7735_MADCTL      = 0x36
# ST7735_PIXFMT      = 0x3A
ST7735_COLMOD       = 0x3A

ST7735_FRMCTR1     = 0xB1
ST7735_FRMCTR2     = 0xB2
ST7735_FRMCTR3     = 0xB3
ST7735_INVCTR      = 0xB4
# ILI9341_DFUNCTR     = 0xB6
ST7735_DISSET5      = 0xB6


ST7735_PWCTR1      = 0xC0
ST7735_PWCTR2      = 0xC1
ST7735_PWCTR3      = 0xC2
ST7735_PWCTR4      = 0xC3
ST7735_PWCTR5      = 0xC4
ST7735_VMCTR1      = 0xC5
# ILI9341_VMCTR2      = 0xC7

ST7735_RDID1       = 0xDA
ST7735_RDID2       = 0xDB
ST7735_RDID3       = 0xDC
ST7735_RDID4       = 0xDD

ST7735_GMCTRP1     = 0xE0
ST7735_GMCTRN1     = 0xE1

ST7735_PWCTR6      = 0xFC

# Colours for convenience
ST7735_BLACK       = 0x0000 # 0b 00000 000000 00000
ST7735_BLUE        = 0x001F # 0b 00000 000000 11111
ST7735_GREEN       = 0x07E0 # 0b 00000 111111 00000
ST7735_RED         = 0xF800 # 0b 11111 000000 00000
ST7735_CYAN        = 0x07FF # 0b 00000 111111 11111
ST7735_MAGENTA     = 0xF81F # 0b 11111 000000 11111
ST7735_YELLOW      = 0xFFE0 # 0b 11111 111111 00000
ST7735_WHITE       = 0xFFFF # 0b 11111 111111 11111


# Pin definition
LCD_RST_PIN         = 27
LCD_DC_PIN          = 25
LCD_CS_PIN          = 8
LCD_BL_PIN          = 24

# Set LCD_WIDTH, LCD_HEIGHT
LCD_1IN44 = 0
LCD_1IN8 = 1
if LCD_1IN44 == 1:
    LCD_WIDTH  = 128  #LCD width
    LCD_HEIGHT = 128 #LCD height

if LCD_1IN8 == 1:
    LCD_WIDTH  = 160
    LCD_HEIGHT = 128

LCD_X = 2
LCD_Y = 1
LCD_X_MAXPIXEL = 132  #LCD width maximum memory
LCD_Y_MAXPIXEL = 162  #LCD height maximum memory

# LCD scanning method
L2R_U2D = 1
L2R_D2U = 2
R2L_U2D = 3
R2L_D2U = 4
U2D_L2R = 5
U2D_R2L = 6
D2U_L2R = 7
D2U_R2L = 8
SCAN_DIR_DFT = U2D_R2L

# SPI device, bus = 0, device = 0

SPI = spidev.SpiDev(0, 0)

def epd_digital_write(pin, value):
    GPIO.output(pin, value)

def delay_ms(xms):
    time.sleep(xms / 1000.0)

class ST7735(object):
    """Representation of an ST7735 TFT LCD."""

    def __init__(self,
                 dc=LCD_DC_PIN,
                 rst=LCD_RST_PIN,
                 cs=LCD_CS_PIN,
                 bl=LCD_BL_PIN,
                 width=LCD_WIDTH,
                 height=LCD_HEIGHT):
        """Create an instance of the display using SPI communication.  Must
        provide the GPIO pin number for the D/C pin and the SPI driver.  Can
        optionally provide the GPIO pin number for the reset pin as the rst
        parameter.
        """

        print("initializing LCD_ST7735")

        self._dc = dc
        self._rst = rst
        self._cs = cs
        self._bl = bl
        self.width = width
        self.height = height
        self.scan_direction = SCAN_DIR_DFT
        self.LCD_X_Adjust = LCD_X
        self.LCD_Y_Adjust = LCD_Y

        # set up i/o pins
        self.GPIO_init()

        # Create an image buffer.
        self.buffer = Image.new('RGB', (width, height))

    def GPIO_init(self):
        """Initialize GPIO pins for ST7735 comms"""

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._rst, GPIO.OUT)
        GPIO.setup(self._dc, GPIO.OUT)
        GPIO.setup(self._cs, GPIO.OUT)
        GPIO.setup(self._bl, GPIO.OUT)
        SPI.max_speed_hz = SPI_CLOCK_HZ
        SPI.mode = 0b00
        return 0;

    def color565(self, r, g, b):
        """Convert red, green, blue components to a 16-bit 565 RGB value. Components
        should be values 0 to 255.
        """
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    # numpy is fastest way to convert image to bytes
    def image_to_data(self, image):
        """Generator function to convert a PIL image to 16-bit 565 RGB bytes."""
        # NumPy is much faster at doing this. NumPy code provided by:
        # Keith (https://www.blogger.com/profile/02555547344016007163)
        pb = np.array(image.convert('RGB')).astype('uint16')
        color = ((pb[:,:,0] & 0xF8) << 8) | ((pb[:,:,1] & 0xFC) << 3) | (pb[:,:,2] >> 3)
        return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()

    def send(self, data, is_data=True, chunk_size=4096):
        """Write a byte or array of bytes to the display. Is_data parameter
        controls if byte should be interpreted as display data (True) or command
        data (False).  Chunk_size is an optional size of bytes to write in a
        single SPI transaction, with a default of 4096.
        """
        # Set DC low for command, high for data.
        GPIO.output(self._dc, is_data)
        # Convert scalar argument to list so either can be passed as parameter.
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        # Write data a chunk at a time.
        for start in range(0, len(data), chunk_size):
            end = min(start+chunk_size, len(data))
            SPI.writebytes(data[start:end])

    def send_command(self, data):
        """Write a byte or array of bytes to the display as command data."""
        self.send(data, False)

    def send_data(self, data):
        """Write a byte or array of bytes to the display as display data."""
        self.send(data, True)

    def send_byte(self, byte):
        GPIO.output(self._dc, True)
        SPI.writebytes([byte])

    def clear(self, color=(0,0,0)):
        """Clear the image buffer to the specified RGB color (default black)."""
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

    def draw(self):
        """Return a PIL ImageDraw instance for 2D drawing on the image buffer."""
        return ImageDraw.Draw(self.buffer)

    def WriteData_NLen16Bit(self, Data, DataLen):
        GPIO.output(self._dc, GPIO.HIGH)
        for i in range(0, DataLen):
            SPI.writebytes([Data >> 8])
            SPI.writebytes([Data & 0xff])

    """    Common register initialization    """
    def LCD_InitReg(self):
        #ST7735R Frame Rate
        self.send_command(ST7735_FRMCTR1)
        self.send_data([ 0x01, 0x2C, 0x2D])

        self.send_command(ST7735_FRMCTR2)
        self.send_data([ 0x01, 0x2C, 0x2D])

        self.send_command(ST7735_FRMCTR3)
        self.send_data([ 0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])

        #Column inversion
        self.send_command(ST7735_INVCTR)
        self.send_byte(0x07)

        #ST7735R Power Sequence
        self.send_command(ST7735_PWCTR1)
        self.send_data([ 0xA2, 0x02, 0x84])
        self.send_command(ST7735_PWCTR2)
        self.send_byte(0xC5)

        self.send_command(ST7735_PWCTR3)
        self.send_data([ 0x0A, 0x00])

        self.send_command(ST7735_PWCTR4)
        self.send_data([ 0x8A, 0x2A])
        self.send_command(ST7735_PWCTR5)
        self.send_data([ 0x8A, 0xEE ])

        self.send_command(ST7735_VMCTR1)#VCOM
        self.send_byte(0x0E)

        #ST7735R Gamma Sequence
        self.send_command(ST7735_GMCTRP1)
        self.send_data([ 0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
                         0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])

        self.send_command(ST7735_GMCTRN1)
        self.send_data([ 0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
                         0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])

        #Enable test command
        self.send_command(0xF0)
        self.send_byte(0x01)

        #Disable ram power save mode
        self.send_command(0xF6)
        self.send_byte(0x00)

        #65k mode
        self.send_command(0x3A)
        self.send_byte(0x05)

    #********************************************************************************
    #function:  Set the display scan and color transfer modes
    #********************************************************************************
    def set_scan(self):
        #Get GRAM and LCD width and height
        if ((self.scan_direction == L2R_U2D) or
            (self.scan_direction == L2R_D2U) or
            (self.scan_direction == R2L_U2D) or
            (self.scan_direction == R2L_D2U)) :
            self.width  = LCD_HEIGHT
            self.height     = LCD_WIDTH
            self.LCD_X_Adjust = LCD_X
            self.LCD_Y_Adjust = LCD_Y
            if self.scan_direction == L2R_U2D:
                MemoryAccessReg_Data = 0X00 | 0x00
            elif self.scan_direction == L2R_D2U:
                MemoryAccessReg_Data = 0X00 | 0x80
            elif self.scan_direction == R2L_U2D:
                MemoryAccessReg_Data = 0x40 | 0x00
            else:       #R2L_D2U:
                MemoryAccessReg_Data = 0x40 | 0x80
        else:
            self.width  = LCD_WIDTH
            self.height     = LCD_HEIGHT
            self.LCD_X_Adjust = LCD_Y
            self.LCD_Y_Adjust = LCD_X
            if self.scan_direction == U2D_L2R:
                MemoryAccessReg_Data = 0X00 | 0x00 | 0x20
            elif self.scan_direction == U2D_R2L:
                MemoryAccessReg_Data = 0X00 | 0x40 | 0x20
            elif self.scan_direction == D2U_L2R:
                MemoryAccessReg_Data = 0x80 | 0x00 | 0x20
            else:       #R2L_D2U
                MemoryAccessReg_Data = 0x40 | 0x80 | 0x20

        # Set the read / write scan direction of the frame memory
        self.send_command(ST7735_MADCTL)     #MX, MY, RGB mode
        if LCD_1IN44 == 1:
            self.send_byte( MemoryAccessReg_Data | 0x08)    #0x08 set RGB
        else:
            self.send_byte( MemoryAccessReg_Data & 0xf7)    #RGB color filter panel

    #/********************************************************************************
    #function:  Set the display point (Xpoint, Ypoint)
    #parameter:
    #       xStart :   X direction Start coordinates
    #       xEnd   :   X direction end coordinates
    #********************************************************************************/
    def LCD_SetCursor (self, Xpoint, Ypoint ):
        self.set_window ( Xpoint, Ypoint, Xpoint , Ypoint )

    #/********************************************************************************
    #function:  Set show color
    #parameter:
    #       Color  :   Set show color
    #********************************************************************************/
    def LCD_SetColor(self, Color , width,  height):
        self.WriteData_NLen16Bit(Color,width * height)

    #/********************************************************************************
    #function:  Point (Xpoint, Ypoint) Fill the color
    #parameter:
    #       Xpoint :   The x coordinate of the point
    #       Ypoint :   The y coordinate of the point
    #       Color  :   Set the color
    #********************************************************************************/
    def LCD_SetPointlColor (self,  Xpoint,  Ypoint, Color ):
        if ( ( Xpoint <= self.width ) and ( Ypoint <= self.height ) ):
            self.LCD_SetCursor (Xpoint, Ypoint)
            self.LCD_SetColor ( Color , 1 , 1)

    #/********************************************************************************
    #function:  Fill the area with the color
    #parameter:
    #       Xstart :   Start point x coordinate
    #       Ystart :   Start point y coordinate
    #       Xend   :   End point coordinates
    #       Yend   :   End point coordinates
    #       Color  :   Set the color
    #********************************************************************************/
    def LCD_SetArealColor (self, Xstart, Ystart, Xend, Yend, Color):
        if (Xend > Xstart) and (Yend > Ystart):
            self.set_window( Xstart , Ystart , Xend , Yend  )
            self.LCD_SetColor ( Color ,Xend - Xstart , Yend - Ystart )

    #/********************************************************************************
    #function:
    #           Clear screen
    #********************************************************************************/
    def LCD_Clear(self):
        if ((self.scan_direction == L2R_U2D) or
                    (self.scan_direction == L2R_D2U) or
                    (self.scan_direction == R2L_U2D) or
                    (self.scan_direction == R2L_D2U)) :
            self.LCD_SetArealColor(0,0, LCD_X_MAXPIXEL , LCD_Y_MAXPIXEL  , Color = 0xFFFF)#white
        else:
            self.LCD_SetArealColor(0,0, LCD_Y_MAXPIXEL , LCD_X_MAXPIXEL  , Color = 0xFFFF)#white

    #/********************************************************************************
    #function:
    #           initialization
    #********************************************************************************/
    def begin(self): # was LCD_Init
        if (self.GPIO_init() != 0):
            return -1

        #Turn on the backlight
        GPIO.output( self._bl, GPIO.HIGH)

        #Hardware reset
        self.reset()

        #Set the initialization register
        self.LCD_InitReg()

        #Set the display scan and color transfer modes
        self.set_scan()
        delay_ms(200)

        #sleep out
        self.send_command(ST7735_SLPOUT)
        delay_ms(120)

        #Turn on the LCD display
        self.send_command(ST7735_DISPON)

        self.LCD_Clear()

    #/********************************************************************************
    #function:  Sets the start position and size of the display area
    #parameter:
    #   Xstart  :   X direction Start coordinates
    #   Ystart  :   Y direction Start coordinates
    #   Xend    :   X direction end coordinates
    #   Yend    :   Y direction end coordinates
    #********************************************************************************/
    def set_window(self, Xstart, Ystart, Xend, Yend ): # was LCD_SetWindows
        # set the X coordinates
        self.send_command( ST7735_CASET )

                # Set the horizontal starting point to the high octet
        self.send_byte( 0x00 )

                # Set the horizontal starting point to the low octet
        self.send_byte( (Xstart & 0xff) + self.LCD_X_Adjust)

                # Set the horizontal end to the high octet
        self.send_byte( 0x00 )

                # Set the horizontal end to the low octet
        self.send_byte( (( Xend - 1 ) & 0xff) + self.LCD_X_Adjust)

        #set the Y coordinates
        self.send_command( ST7735_RASET )
        self.send_data([ 0x00, (Ystart & 0xff) + self.LCD_Y_Adjust,
                         0x00, ( (Yend - 1) & 0xff )+ self.LCD_Y_Adjust ])

        self.send_command( ST7735_RAMWR )

    def reset(self):
        """Reset the display, if reset pin is connected."""
        if self._rst is not None:
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.100)
            GPIO.output(self._rst, GPIO.LOW)
            time.sleep(0.100)
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.100)

    # -----------------------------------------------------------------------
    # Display a full-screen image
    # -----------------------------------------------------------------------
    def display(self, image=None):
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # By default write the internal buffer to the display.
        if image is None:
            image = self.buffer
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
        """Write the display buffer or provided image to the hardware.  If no
        image parameter is provided the display buffer will be written to the
        hardware.  If an image is provided, it should be RGB format and the
        same dimensions as the display hardware.
        """
        # By default write the internal buffer to the display.
        if image is None:
            image = self.buffer
        # Set address bounds to entire display.
        self.set_window( x, y, x+w, y+h)
        # Convert image to array of 16bit 565 RGB data bytes.
        # Unfortunate that this copy has to occur, but the SPI byte writing
        # function needs to take an array of bytes and PIL doesn't natively
        # store images in 16-bit 565 RGB format.
        pixelbytes = list(self.image_to_data(image))
        # Write data to hardware.
        self.send_data(pixelbytes)

