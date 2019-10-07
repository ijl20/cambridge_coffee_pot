# Cambridge Coffee Pot

![Original Trojan Room coffee pot image](Trojan_Room_coffee_pot_xcoffee.png)

## The concept

Build a sensor set that measures and transmits in real-time the coffee-making
and consuming events happening on the Computer Lab Cambridge Coffee Pot.

This is actually monitoring the direct descendant of the original
Cambridge [Trojan Room coffee pot](https://en.wikipedia.org/wiki/Trojan_Room_coffee_pot)
from 1991 to 2001.

## Sensors

### Raspberry Pi based weight sensor

This uses a Raspberry Pi (Model 3 B+) with two 5Kg load cells connected via
a HX711 A/D converter, and also a Waveshare 1.8inch color LCD module for a
local display.

#### Raspberry Pi

![Pi 3 B+ GPIO pinout](raspberry_pi/gpio.png)

#### Load cells for weight sensing the coffee pot

E.g. [available Amazon UK](https://www.amazon.co.uk/gp/product/B07GRGT3C3)

#### HX711 A/D converter for load cells

[HX711 Data sheet](hx711/hx711_english.pdf)

#### Waveshare 1.8inch color LCD module

E.g. [available Amazon UK](https://www.amazon.co.uk/Waveshare-1-8inch-LCD-Module/dp/B077YFTMVT)

[Online info](https://www.waveshare.com/wiki/1.8inch_LCD_Module)

----
Quick code credited to [underdoeg](https://github.com/underdoeg/)'s [Gist HX711.py](https://gist.github.com/underdoeg/98a38b54f889fce2b237).
I've only made a few modifications on the way the captured bits are processed and to support Two's Complement, which it didn't.

Instructions
------------
Check example.py to see how it works.

Installation
------------
1. Clone or download and unpack this repository
2. In the repository directory, run
```
python setup.py install
```

Using a 2-channel HX711 module
------------------------------
Channel A has selectable gain of 128 or 64.  Using set_gain(128) or set_gain(64)
selects channel A with the specified gain.

Using set_gain(32) selects channel B at the fixed gain of 32.  The tare_B(),
get_value_B() and get_weight_B() functions do this for you.

This info was obtained from an HX711 datasheet located at
https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf

### wifi Power monitors for the coffee percolator and the grinder


