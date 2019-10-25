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

class LCD_ST7735(object):
    """Representation of an ST7735 TFT LCD."""

    def __init__(self,
                 dc=LCD_DC_PIN,
                 rst=LCD_RST_PIN,
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
        GPIO.setup(LCD_RST_PIN, GPIO.OUT)
        GPIO.setup(LCD_DC_PIN, GPIO.OUT)
        GPIO.setup(LCD_CS_PIN, GPIO.OUT)
        GPIO.setup(LCD_BL_PIN, GPIO.OUT)
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

    def reset(self):
        """Reset the display, if reset pin is connected."""
        if self._rst is not None:
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.100)
            GPIO.output(self._rst, GPIO.LOW)
            time.sleep(0.100)
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.100)

    def OLD_init(self):
        # Initialize the display.  Broken out as a separate function so it can
        # be overridden by other displays in the future.

        self.send_command(ST7735_SWRESET) # Software reset
        time.sleep(0.150) # delay 150 ms

        self.send_command(ST7735_SLPOUT) # Out of sleep mode
        time.sleep(0.500) # delay 500 ms

        self.send_command(ST7735_FRMCTR1) # Frame rate ctrl - normal mode
        self.send_data(0x01) # Rate = fosc/(1x2+40) * (LINE+2C+2D)
        self.send_data(0x2C)
        self.send_data(0x2D)

        self.send_command(ST7735_FRMCTR2) # Frame rate ctrl - idle mode
        self.send_data(0x01) # Rate = fosc/(1x2+40) * (LINE+2C+2D)
        self.send_data(0x2C)
        self.send_data(0x2D)

        self.send_command(ST7735_FRMCTR3) # Frame rate ctrl - partial mode
        self.send_data(0x01) # Dot inversion mode
        self.send_data(0x2C)
        self.send_data(0x2D)
        self.send_data(0x01) # Line inversion mode
        self.send_data(0x2C)
        self.send_data(0x2D)

        self.send_command(ST7735_INVCTR) # Display inversion ctrl
        self.send_data(0x07) # No inversion

        self.send_command(ST7735_PWCTR1) # Power control
        self.send_data(0xA2)
        self.send_data(0x02) # -4.6V
        self.send_data(0x84) # auto mode

        self.send_command(ST7735_PWCTR2) # Power control
        self.send_data(0x0A) # Opamp current small
        self.send_data(0x00) # Boost frequency

        self.send_command(ST7735_PWCTR4) # Power control
        self.send_data(0x8A) # BCLK/2, Opamp current small & Medium low
        self.send_data(0x2A)

        self.send_command(ST7735_PWCTR5) # Power control
        self.send_data(0x8A)
        self.send_data(0xEE)

        self.send_command(ST7735_VMCTR1) # Power control
        self.send_data(0x0E)

        self.send_command(ST7735_INVOFF) # Don't invert display

        self.send_command(ST7735_MADCTL) # Memory access control (directions)
        self.send_data(0xC8) # row addr/col addr, bottom to top refresh

        self.send_command(ST7735_COLMOD) # set color mode
        self.send_data(0x05) # 16-bit color

        #

        self.send_command(ST7735_CASET) # Column addr set
        self.send_data(0x00) # XSTART = 0
        self.send_data(0x00)
        self.send_data(0x00) # XEND = 127
        self.send_data(0x7F)

        self.send_command(ST7735_RASET) # Row addr set
        self.send_data(0x00) # XSTART = 0
        self.send_data(0x00)
        self.send_data(0x00) # XEND = 159
        self.send_data(0x9F)

        #

        self.send_command(ST7735_GMCTRP1) # Set Gamma
        self.send_data(0x02)
        self.send_data(0x1c)
        self.send_data(0x07)
        self.send_data(0x12)
        self.send_data(0x37)
        self.send_data(0x32)
        self.send_data(0x29)
        self.send_data(0x2d)
        self.send_data(0x29)
        self.send_data(0x25)
        self.send_data(0x2B)
        self.send_data(0x39)
        self.send_data(0x00)
        self.send_data(0x01)
        self.send_data(0x03)
        self.send_data(0x10)

        self.send_command(ST7735_GMCTRN1) # Set Gamma
        self.send_data(0x03)
        self.send_data(0x1d)
        self.send_data(0x07)
        self.send_data(0x06)
        self.send_data(0x2E)
        self.send_data(0x2C)
        self.send_data(0x29)
        self.send_data(0x2D)
        self.send_data(0x2E)
        self.send_data(0x2E)
        self.send_data(0x37)
        self.send_data(0x3F)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x02)
        self.send_data(0x10)

        self.send_command(ST7735_NORON) # Normal display on
        time.sleep(0.10) # 10 ms

        self.send_command(ST7735_DISPON) # Display on
        time.sleep(0.100) # 100 ms

    def OLD_begin(self):
        """Initialize the display.  Should be called once before other calls that
        interact with the display are called.
        """
        self.reset()
        self._init()

    def OLD_set_window(self, x0=0, y0=0, x1=None, y1=None):
        """Set the pixel address window for proceeding drawing commands. x0 and
        x1 should define the minimum and maximum x pixel bounds.  y0 and y1
        should define the minimum and maximum y pixel bound.  If no parameters
        are specified the default will be to update the entire display from 0,0
        to width-1,height-1.
        """
        if x1 is None:
            x1 = self.width-1
        if y1 is None:
            y1 = self.height-1
        self.send_command(ST7735_CASET)        # Column addr set
        self.send_data(x0 >> 8)
        self.send_data(x0)                    # XSTART
        self.send_data(x1 >> 8)
        self.send_data(x1)                    # XEND
        self.send_command(ST7735_RASET)        # Row addr set
        self.send_data(y0 >> 8)
        self.send_data(y0)                    # YSTART
        self.send_data(y1 >> 8)
        self.send_data(y1)                    # YEND
        self.send_command(ST7735_RAMWR)        # write to RAM

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

    def clear(self, color=(0,0,0)):
        """Clear the image buffer to the specified RGB color (default black)."""
        width, height = self.buffer.size
        self.buffer.putdata([color]*(width*height))

    def draw(self):
        """Return a PIL ImageDraw instance for 2D drawing on the image buffer."""
        return ImageDraw.Draw(self.buffer)

    """    Hardware reset     """
    def OLD_Reset(self):
        GPIO.output(LCD_RST_PIN, GPIO.HIGH)
        delay_ms(100)
        GPIO.output(LCD_RST_PIN, GPIO.LOW)
        delay_ms(100)
        GPIO.output(LCD_RST_PIN, GPIO.HIGH)
        delay_ms(100)

    """    Write register address and data     """
    def WriteCommand(self, Reg):
        GPIO.output(LCD_DC_PIN, GPIO.LOW)
        SPI.writebytes([Reg])

    def WriteByte(self, Data):
        GPIO.output(LCD_DC_PIN, GPIO.HIGH)
        SPI.writebytes([Data])

    def WriteData_NLen16Bit(self, Data, DataLen):
        GPIO.output(LCD_DC_PIN, GPIO.HIGH)
        for i in range(0, DataLen):
            SPI.writebytes([Data >> 8])
            SPI.writebytes([Data & 0xff])

    """    Common register initialization    """
    def LCD_InitReg(self):
        #ST7735R Frame Rate
        self.WriteCommand(ST7735_FRMCTR1)
        self.WriteByte(0x01)
        self.WriteByte(0x2C)
        self.WriteByte(0x2D)

        self.WriteCommand(ST7735_FRMCTR2)
        self.WriteByte(0x01)
        self.WriteByte(0x2C)
        self.WriteByte(0x2D)

        self.WriteCommand(ST7735_FRMCTR3)
        self.WriteByte(0x01)
        self.WriteByte(0x2C)
        self.WriteByte(0x2D)
        self.WriteByte(0x01)
        self.WriteByte(0x2C)
        self.WriteByte(0x2D)

        #Column inversion
        self.WriteCommand(ST7735_INVCTR)
        self.WriteByte(0x07)

        #ST7735R Power Sequence
        self.WriteCommand(ST7735_PWCTR1)
        self.WriteByte(0xA2)
        self.WriteByte(0x02)
        self.WriteByte(0x84)
        self.WriteCommand(ST7735_PWCTR2)
        self.WriteByte(0xC5)

        self.WriteCommand(ST7735_PWCTR3)
        self.WriteByte(0x0A)
        self.WriteByte(0x00)

        self.WriteCommand(ST7735_PWCTR4)
        self.WriteByte(0x8A)
        self.WriteByte(0x2A)
        self.WriteCommand(ST7735_PWCTR5)
        self.WriteByte(0x8A)
        self.WriteByte(0xEE)

        self.WriteCommand(ST7735_VMCTR1)#VCOM
        self.WriteByte(0x0E)

        #ST7735R Gamma Sequence
        self.WriteCommand(ST7735_GMCTRP1)
        self.WriteByte(0x0f)
        self.WriteByte(0x1a)
        self.WriteByte(0x0f)
        self.WriteByte(0x18)
        self.WriteByte(0x2f)
        self.WriteByte(0x28)
        self.WriteByte(0x20)
        self.WriteByte(0x22)
        self.WriteByte(0x1f)
        self.WriteByte(0x1b)
        self.WriteByte(0x23)
        self.WriteByte(0x37)
        self.WriteByte(0x00)
        self.WriteByte(0x07)
        self.WriteByte(0x02)
        self.WriteByte(0x10)

        self.WriteCommand(ST7735_GMCTRN1)
        self.WriteByte(0x0f)
        self.WriteByte(0x1b)
        self.WriteByte(0x0f)
        self.WriteByte(0x17)
        self.WriteByte(0x33)
        self.WriteByte(0x2c)
        self.WriteByte(0x29)
        self.WriteByte(0x2e)
        self.WriteByte(0x30)
        self.WriteByte(0x30)
        self.WriteByte(0x39)
        self.WriteByte(0x3f)
        self.WriteByte(0x00)
        self.WriteByte(0x07)
        self.WriteByte(0x03)
        self.WriteByte(0x10)

        #Enable test command
        self.WriteCommand(0xF0)
        self.WriteByte(0x01)

        #Disable ram power save mode
        self.WriteCommand(0xF6)
        self.WriteByte(0x00)

        #65k mode
        self.WriteCommand(0x3A)
        self.WriteByte(0x05)

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
        self.WriteCommand(ST7735_MADCTL)     #MX, MY, RGB mode
        if LCD_1IN44 == 1:
            self.WriteByte( MemoryAccessReg_Data | 0x08)    #0x08 set RGB
        else:
            self.WriteByte( MemoryAccessReg_Data & 0xf7)    #RGB color filter panel

    #/********************************************************************************
    #function:
    #           initialization
    #********************************************************************************/
    def begin(self): # was LCD_Init
        if (self.GPIO_init() != 0):
            return -1

        #Turn on the backlight
        GPIO.output(LCD_BL_PIN,GPIO.HIGH)

        #Hardware reset
        self.reset()

        #Set the initialization register
        self.LCD_InitReg()

        #Set the display scan and color transfer modes
        self.set_scan()
        delay_ms(200)

        #sleep out
        self.WriteCommand(ST7735_SLPOUT)
        delay_ms(120)

        #Turn on the LCD display
        self.WriteCommand(ST7735_DISPON)

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
        self.WriteCommand( ST7735_CASET )

                # Set the horizontal starting point to the high octet
        self.WriteByte( 0x00 )

                # Set the horizontal starting point to the low octet
        self.WriteByte( (Xstart & 0xff) + self.LCD_X_Adjust)

                # Set the horizontal end to the high octet
        self.WriteByte( 0x00 )

                # Set the horizontal end to the low octet
        self.WriteByte( (( Xend - 1 ) & 0xff) + self.LCD_X_Adjust)

        #set the Y coordinates
        self.WriteCommand( ST7735_RASET )
        self.WriteByte( 0x00 )
        self.WriteByte( (Ystart & 0xff) + self.LCD_Y_Adjust)
        self.WriteByte( 0x00 )
        self.WriteByte( ( (Yend - 1) & 0xff )+ self.LCD_Y_Adjust)

        self.WriteCommand( ST7735_RAMWR )

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
    #           Page Image
        # Writes a display-sized image to the full display
    #********************************************************************************/
    def OLD_PageImage(self,Image): # now display(image)
        if (Image == None):
            return

        self.LCD_SetWindows ( 0, 0, self.width , self.height  )
        Pixels = Image.load()
        for j in range(0, self.height ):
            for i in range(0, self.width ):
                Pixels_Color = (((Pixels[i, j][0] >> 3) << 11) |
                                                ((Pixels[i, j][1] >> 2) << 5) |
                                                (Pixels[i, j][2] >> 3)) #RGB Data
                self.LCD_SetColor(Pixels_Color , 1, 1)

    #/********************************************************************************
    #function:
    #           Show Image
    #********************************************************************************/
    def LCD_ShowWindowImage(self,image,x,y,w,h):
        if (image == None):
            return

        self.set_window ( x, y, x+w , y+h )
        Pixels = image.load()
        for j in range(0, h ):
            for i in range(0, w ):
                Pixels_Color = (((Pixels[i, j][0] >> 3) << 11) |
                                                ((Pixels[i, j][1] >> 2) << 5) |
                                                (Pixels[i, j][2] >> 3)) #RGB Data
                self.LCD_SetColor(Pixels_Color , 1, 1)

