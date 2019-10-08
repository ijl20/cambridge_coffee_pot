
import sys
sys.path.append('LCD_1in8')
import LCD_1in8
import LCD_Config

from PIL  import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

#try:
def main():
    LCD = LCD_1in8.LCD()

    print ("**********Init LCD**********")

    Lcd_ScanDir = LCD_1in8.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
    LCD.LCD_Init(Lcd_ScanDir)

    image = Image.new("RGB", (LCD.LCD_Dis_Column, LCD.LCD_Dis_Page), "WHITE")
    draw = ImageDraw.Draw(image)

    #font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 16)
    print ("***draw line")
    draw.line([(0,0),(159,0)], fill = "BLUE",width = 5)
    draw.line([(159,0),(159,127)], fill = "BLUE",width = 5)
    draw.line([(159,127),(0,127)], fill = "BLUE",width = 5)
    draw.line([(0,127),(0,0)], fill = "BLUE",width = 5)

    print ("***draw rectangle")
    draw.rectangle([(18,10),(142,20)],fill = "RED")

    print ("***draw text")
    draw.text((33, 22), 'Cambridge', fill = "BLUE")
    draw.text((32, 36), 'Coffee', fill = "BLUE")
    draw.text((28, 48), 'Pot', fill = "BLUE")

    LCD.LCD_ShowImage(image,0,0)
    LCD_Config.Driver_Delay_ms(500)

    image = Image.open('example.bmp')
    LCD.LCD_ShowImage(image,0,0)

#while (True):

if __name__ == '__main__':
    main()

#except:
#	print("except")
#	GPIO.cleanup()

