#! /usr/bin/python3

import time
import sys
sys.path.append('hx711')
sys.path.append('LCD_1in8')
import LCD_1in8
import LCD_Config

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageColor

LCD = LCD_1in8.LCD()

font = ImageFont.truetype('fonts/Ubuntu-Regular.ttf', 40)

print ("**********Init LCD**********")

Lcd_ScanDir = LCD_1in8.SCAN_DIR_DFT  #SCAN_DIR_DFT = D2U_L2R
LCD.LCD_Init(Lcd_ScanDir)

image = Image.open('example.bmp')
LCD.LCD_ShowImage(image,0,0)

def update_lcd(weight_g):

    image = Image.new("RGB", (LCD.LCD_Dis_Column, LCD.LCD_Dis_Page), "BLACK")
    draw = ImageDraw.Draw(image)

    #print ("***draw line")
    #draw.line([(0,0),(159,0)], fill = "BLUE",width = 5)
    #draw.line([(159,0),(159,127)], fill = "BLUE",width = 5)
    #draw.line([(159,127),(0,127)], fill = "BLUE",width = 5)
    #draw.line([(0,127),(0,0)], fill = "BLUE",width = 5)

    #print ("***draw rectangle")
    #draw.rectangle([(18,10),(142,20)],fill = "RED")

    #print ("***draw text")
    #draw.text((33, 22), 'Cambridge', fill = "BLUE")
    #draw.text((33, 36), 'Coffee', fill = "BLUE")
    #draw.text((33, 48), 'Pot', fill = "BLUE")

    draw.text((13, 64), "%.1f" % weight_g, fill = "WHITE", font=font, align="right")

    LCD.LCD_ShowImage(image,0,0)
    #LCD_Config.Driver_Delay_ms(500)


EMULATE_HX711=False

referenceUnit = 1

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()

    print("Bye!")
    sys.exit()

hx = HX711(5, 6)

# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
hx.set_reading_format("MSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
#hx.set_reference_unit(113)
hx.set_reference_unit_A(488.1)
hx.set_reference_unit_B(112.4)

hx.reset()

#hx.tare()


# to use both channels, you'll need to tare them both
hx.tare_A()
hx.tare_B()
print("Tare A&B done! Add weight now...")

while True:
    try:
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment these three lines to see what it prints.

        # np_arr8_string = hx.get_np_arr8_string()
        # binary_string = hx.get_binary_string()
        # print binary_string + " " + np_arr8_string

        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
        #val = hx.get_weight(5)
        #print(val)

        # To get weight from both channels (if you have load cells hooked up
        # to both channel A and B), do something like this
        val_A = hx.get_weight_A(1)
        val_B = hx.get_weight_B(1)

        weight_g = val_A + val_B

        print ("A: %s  B: %s TOTAL: %s" % ( val_A, val_B, weight_g ))

        update_lcd(weight_g)

        #hx.power_down()
        #hx.power_up()
        time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()

