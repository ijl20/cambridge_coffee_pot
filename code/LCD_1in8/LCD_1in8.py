 # -*- coding:UTF-8 -*-
 ##
 # | file      	:	LCD_1IN44.py
 # |	version		:	V1.0
 # | date		:	2017-08-16
 # | function	:	On the ST7735S chip driver and clear screen, drawing lines, drawing, writing 
 #					and other functions to achieve
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 #
print("Loading LCD_1in8.py")

import LCD_Config
import RPi.GPIO as GPIO

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

#scanning method
L2R_U2D = 1
L2R_D2U = 2
R2L_U2D = 3
R2L_D2U = 4
U2D_L2R = 5
U2D_R2L = 6
D2U_L2R = 7
D2U_R2L = 8
SCAN_DIR_DFT = U2D_R2L

##***********************************************************************************************************************
#------------------------------------------------------------------------
#|\\\																#/|
#|\\\						Drive layer								#/|
#|\\\																#/|
#------------------------------------------------------------------------
#************************************************************************************************************************
class LCD:
	def __init__(self):
		print("LCD __init__")
		self.LCD_Dis_Column = LCD_WIDTH
		self.LCD_Dis_Page = LCD_HEIGHT
		self.LCD_Scan_Dir = SCAN_DIR_DFT
		self.LCD_X_Adjust = LCD_X
		self.LCD_Y_Adjust = LCD_Y

	"""    Hardware reset     """
	def  LCD_Reset(self):
		GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.HIGH)
		LCD_Config.Driver_Delay_ms(100)
		GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.LOW)
		LCD_Config.Driver_Delay_ms(100)
		GPIO.output(LCD_Config.LCD_RST_PIN, GPIO.HIGH)
		LCD_Config.Driver_Delay_ms(100)

	"""    Write register address and data     """
	def  LCD_WriteReg(self, Reg):
		GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.LOW)
		LCD_Config.SPI_Write_Byte([Reg])

	def LCD_WriteData_8bit(self, Data):
		GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
		LCD_Config.SPI_Write_Byte([Data])

	def LCD_WriteData_NLen16Bit(self, Data, DataLen):
		GPIO.output(LCD_Config.LCD_DC_PIN, GPIO.HIGH)
		for i in range(0, DataLen):
			LCD_Config.SPI_Write_Byte([Data >> 8])
			LCD_Config.SPI_Write_Byte([Data & 0xff])
		
	"""    Common register initialization    """
	def LCD_InitReg(self):
		#ST7735R Frame Rate
		self.LCD_WriteReg(0xB1)
		self.LCD_WriteData_8bit(0x01)
		self.LCD_WriteData_8bit(0x2C)
		self.LCD_WriteData_8bit(0x2D)

		self.LCD_WriteReg(0xB2)
		self.LCD_WriteData_8bit(0x01)
		self.LCD_WriteData_8bit(0x2C)
		self.LCD_WriteData_8bit(0x2D)

		self.LCD_WriteReg(0xB3)
		self.LCD_WriteData_8bit(0x01)
		self.LCD_WriteData_8bit(0x2C)
		self.LCD_WriteData_8bit(0x2D)
		self.LCD_WriteData_8bit(0x01)
		self.LCD_WriteData_8bit(0x2C)
		self.LCD_WriteData_8bit(0x2D)
		
		#Column inversion 
		self.LCD_WriteReg(0xB4)
		self.LCD_WriteData_8bit(0x07)
		
		#ST7735R Power Sequence
		self.LCD_WriteReg(0xC0)
		self.LCD_WriteData_8bit(0xA2)
		self.LCD_WriteData_8bit(0x02)
		self.LCD_WriteData_8bit(0x84)
		self.LCD_WriteReg(0xC1)
		self.LCD_WriteData_8bit(0xC5)

		self.LCD_WriteReg(0xC2)
		self.LCD_WriteData_8bit(0x0A)
		self.LCD_WriteData_8bit(0x00)

		self.LCD_WriteReg(0xC3)
		self.LCD_WriteData_8bit(0x8A)
		self.LCD_WriteData_8bit(0x2A)
		self.LCD_WriteReg(0xC4)
		self.LCD_WriteData_8bit(0x8A)
		self.LCD_WriteData_8bit(0xEE)
		
		self.LCD_WriteReg(0xC5)#VCOM 
		self.LCD_WriteData_8bit(0x0E)
		
		#ST7735R Gamma Sequence
		self.LCD_WriteReg(0xe0)
		self.LCD_WriteData_8bit(0x0f)
		self.LCD_WriteData_8bit(0x1a)
		self.LCD_WriteData_8bit(0x0f)
		self.LCD_WriteData_8bit(0x18)
		self.LCD_WriteData_8bit(0x2f)
		self.LCD_WriteData_8bit(0x28)
		self.LCD_WriteData_8bit(0x20)
		self.LCD_WriteData_8bit(0x22)
		self.LCD_WriteData_8bit(0x1f)
		self.LCD_WriteData_8bit(0x1b)
		self.LCD_WriteData_8bit(0x23)
		self.LCD_WriteData_8bit(0x37)
		self.LCD_WriteData_8bit(0x00)
		self.LCD_WriteData_8bit(0x07)
		self.LCD_WriteData_8bit(0x02)
		self.LCD_WriteData_8bit(0x10)

		self.LCD_WriteReg(0xe1)
		self.LCD_WriteData_8bit(0x0f)
		self.LCD_WriteData_8bit(0x1b)
		self.LCD_WriteData_8bit(0x0f)
		self.LCD_WriteData_8bit(0x17)
		self.LCD_WriteData_8bit(0x33)
		self.LCD_WriteData_8bit(0x2c)
		self.LCD_WriteData_8bit(0x29)
		self.LCD_WriteData_8bit(0x2e)
		self.LCD_WriteData_8bit(0x30)
		self.LCD_WriteData_8bit(0x30)
		self.LCD_WriteData_8bit(0x39)
		self.LCD_WriteData_8bit(0x3f)
		self.LCD_WriteData_8bit(0x00)
		self.LCD_WriteData_8bit(0x07)
		self.LCD_WriteData_8bit(0x03)
		self.LCD_WriteData_8bit(0x10) 
		
		#Enable test command
		self.LCD_WriteReg(0xF0)
		self.LCD_WriteData_8bit(0x01)
		
		#Disable ram power save mode
		self.LCD_WriteReg(0xF6)
		self.LCD_WriteData_8bit(0x00)
		
		#65k mode
		self.LCD_WriteReg(0x3A)
		self.LCD_WriteData_8bit(0x05)

	#********************************************************************************
	#function:	Set the display scan and color transfer modes
	#parameter: 
	#		Scan_dir   :   Scan direction
	#		Colorchose :   RGB or GBR color format
	#********************************************************************************
	def LCD_SetGramScanWay(self, Scan_dir):
		#Get the screen scan direction
		self.LCD_Scan_Dir = Scan_dir
		
		#Get GRAM and LCD width and height
		if (Scan_dir == L2R_U2D) or (Scan_dir == L2R_D2U) or (Scan_dir == R2L_U2D) or (Scan_dir == R2L_D2U) :
			self.LCD_Dis_Column	= LCD_HEIGHT 
			self.LCD_Dis_Page 	= LCD_WIDTH 
			self.LCD_X_Adjust = LCD_X
			self.LCD_Y_Adjust = LCD_Y
			if Scan_dir == L2R_U2D:
				MemoryAccessReg_Data = 0X00 | 0x00
			elif Scan_dir == L2R_D2U:
				MemoryAccessReg_Data = 0X00 | 0x80
			elif Scan_dir == R2L_U2D:
				MemoryAccessReg_Data = 0x40 | 0x00
			else:		#R2L_D2U:
				MemoryAccessReg_Data = 0x40 | 0x80
		else:
			self.LCD_Dis_Column	= LCD_WIDTH 
			self.LCD_Dis_Page 	= LCD_HEIGHT 
			self.LCD_X_Adjust = LCD_Y
			self.LCD_Y_Adjust = LCD_X
			if Scan_dir == U2D_L2R:
				MemoryAccessReg_Data = 0X00 | 0x00 | 0x20
			elif Scan_dir == U2D_R2L:
				MemoryAccessReg_Data = 0X00 | 0x40 | 0x20
			elif Scan_dir == D2U_L2R:
				MemoryAccessReg_Data = 0x80 | 0x00 | 0x20
			else:		#R2L_D2U
				MemoryAccessReg_Data = 0x40 | 0x80 | 0x20
		
		# Set the read / write scan direction of the frame memory
		self.LCD_WriteReg(0x36)		#MX, MY, RGB mode 
		if LCD_1IN44 == 1:
			self.LCD_WriteData_8bit( MemoryAccessReg_Data | 0x08)	#0x08 set RGB
		else:
			self.LCD_WriteData_8bit( MemoryAccessReg_Data & 0xf7)	#RGB color filter panel

	#/********************************************************************************
	#function:	
	#			initialization
	#********************************************************************************/
	def LCD_Init(self, Lcd_ScanDir):
		if (LCD_Config.GPIO_Init() != 0):
			return -1
		
		#Turn on the backlight
		GPIO.output(LCD_Config.LCD_BL_PIN,GPIO.HIGH)
		
		#Hardware reset
		self.LCD_Reset()
		
		#Set the initialization register
		self.LCD_InitReg()
		
		#Set the display scan and color transfer modes	
		self.LCD_SetGramScanWay( Lcd_ScanDir )
		LCD_Config.Driver_Delay_ms(200)
		
		#sleep out
		self.LCD_WriteReg(0x11)
		LCD_Config.Driver_Delay_ms(120)
		
		#Turn on the LCD display
		self.LCD_WriteReg(0x29)
		
		self.LCD_Clear()

	#/********************************************************************************
	#function:	Sets the start position and size of the display area
	#parameter: 
	#	Xstart 	:   X direction Start coordinates
	#	Ystart  :   Y direction Start coordinates
	#	Xend    :   X direction end coordinates
	#	Yend    :   Y direction end coordinates
	#********************************************************************************/
	def LCD_SetWindows(self, Xstart, Ystart, Xend, Yend ):
		#set the X coordinates
		self.LCD_WriteReg ( 0x2A )
		self.LCD_WriteData_8bit ( 0x00 )											#Set the horizontal starting point to the high octet
		self.LCD_WriteData_8bit ( (Xstart & 0xff) + self.LCD_X_Adjust)			#Set the horizontal starting point to the low octet
		self.LCD_WriteData_8bit ( 0x00 )											#Set the horizontal end to the high octet
		self.LCD_WriteData_8bit ( (( Xend - 1 ) & 0xff) + self.LCD_X_Adjust)		#Set the horizontal end to the low octet

		#set the Y coordinates
		self.LCD_WriteReg ( 0x2B )
		self.LCD_WriteData_8bit ( 0x00 )
		self.LCD_WriteData_8bit ( (Ystart & 0xff) + self.LCD_Y_Adjust)
		self.LCD_WriteData_8bit ( 0x00 )
		self.LCD_WriteData_8bit ( ( (Yend - 1) & 0xff )+ self.LCD_Y_Adjust)

		self.LCD_WriteReg(0x2C)	

	#/********************************************************************************
	#function:	Set the display point (Xpoint, Ypoint)
	#parameter: 
	#		xStart :   X direction Start coordinates
	#		xEnd   :   X direction end coordinates
	#********************************************************************************/
	def LCD_SetCursor (self, Xpoint, Ypoint ):
		self.LCD_SetWindows ( Xpoint, Ypoint, Xpoint , Ypoint )

	#/********************************************************************************
	#function:	Set show color
	#parameter: 
	#		Color  :   Set show color
	#********************************************************************************/
	def LCD_SetColor(self, Color , width,  height):
		self.LCD_WriteData_NLen16Bit(Color,width * height)

	#/********************************************************************************
	#function:	Point (Xpoint, Ypoint) Fill the color
	#parameter: 
	#		Xpoint :   The x coordinate of the point
	#		Ypoint :   The y coordinate of the point
	#		Color  :   Set the color
	#********************************************************************************/
	def LCD_SetPointlColor (self,  Xpoint,  Ypoint, Color ):
		if ( ( Xpoint <= self.LCD_Dis_Column ) and ( Ypoint <= self.LCD_Dis_Page ) ):
			self.LCD_SetCursor (Xpoint, Ypoint)
			self.LCD_SetColor ( Color , 1 , 1)

	#/********************************************************************************
	#function:	Fill the area with the color
	#parameter: 
	#		Xstart :   Start point x coordinate
	#		Ystart :   Start point y coordinate
	#		Xend   :   End point coordinates
	#		Yend   :   End point coordinates
	#		Color  :   Set the color
	#********************************************************************************/
	def LCD_SetArealColor (self, Xstart, Ystart, Xend, Yend, Color):
		if (Xend > Xstart) and (Yend > Ystart):
			self.LCD_SetWindows( Xstart , Ystart , Xend , Yend  )
			self.LCD_SetColor ( Color ,Xend - Xstart , Yend - Ystart )

	#/********************************************************************************
	#function:	
	#			Clear screen 
	#********************************************************************************/
	def LCD_Clear(self):
		if (self.LCD_Scan_Dir == L2R_U2D) or (self.LCD_Scan_Dir == L2R_D2U) or (self.LCD_Scan_Dir == R2L_U2D) or (self.LCD_Scan_Dir == R2L_D2U) :
			self.LCD_SetArealColor(0,0, LCD_X_MAXPIXEL , LCD_Y_MAXPIXEL  , Color = 0xFFFF)#white
		else:
			self.LCD_SetArealColor(0,0, LCD_Y_MAXPIXEL , LCD_X_MAXPIXEL  , Color = 0xFFFF)#white
	def LCD_ShowImage(self,Image,Xstart,Ystart):
		if (Image == None):
			return

		self.LCD_SetWindows ( 0, 0, self.LCD_Dis_Column , self.LCD_Dis_Page  )
		Pixels = Image.load()
		for j in range(0, self.LCD_Dis_Page ):
			for i in range(0, self.LCD_Dis_Column ):
				Pixels_Color = ((Pixels[i, j][0] >> 3) << 11)|((Pixels[i, j][1] >> 2) << 5)|(Pixels[i, j][2] >> 3)#RGB Data
				self.LCD_SetColor(Pixels_Color , 1, 1)
				