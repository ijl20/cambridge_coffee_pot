# Cambridge Coffee Pot

![Original Trojan Room coffee pot image](images/Trojan_Room_coffee_pot_xcoffee.png)
![Current Netos coffee pot image 2019-10-08](images/kitchen.jpg)


## The concept

Build a sensor set that measures and transmits in real-time the coffee-making
and consuming events happening on the Computer Lab Cambridge Coffee Pot.

This is actually monitoring the direct descendant of the original
Cambridge [Trojan Room coffee pot](https://en.wikipedia.org/wiki/Trojan_Room_coffee_pot)
from 1991 to 2001.

![whiteboard sketch Ian Lewis and Brian Jones](images/whiteboard_design.jpg)

## Prototype

2019-10-09
![William Gates Building Ian Lewis office FE11 sensor prototype](images/prototype.jpg)


It will take weight measurements as in the sample data illustrated below, and recognize events
such as a fresh pot of coffee being placed. The objective is that these events are communicated
to the server with the minimum latency.

![data chart of weight load with time for full coffe pot plus pouring 1 cup](data/sample_weights_fill_plus_1_cup.png)

## Development install

```
git clone https://github.com/ijl20/cambridge_coffee_pot
```

This repo includes working python libraries for:

* the hx711 D/A chip commonly used to connect load cells (code/hx711_ijl20/hx711.py)
* the st7735 LCD drive chip commonly used with inexpensive small LCD displays (code/st7735_ijl20/st7735.py)

The ```code``` directory contains a bunch of other libraries for the hx711 and the st7735 which were a reasonable source of clues but needed improvement.

Python support for http POST of sensor data:

```
pip install requests
```

## Components

### CPU

For this one-off experimental sensor we used a Raspberry Pi 3B+, using the GPIO pins to
connect the LCD display (via SPI) and the two load cell A/D converters (each needing +Vcc, GND and two data
pins)

![Pi 3 B+ GPIO pinout](images/pi_3_gpio.png)

### Weight sensor

Two 5Kg load cells connected via two HX711 A/D converters.

### LCD Display - Waveshare 1.8inch color LCD module

[Online info](https://www.waveshare.com/wiki/1.8inch_LCD_Module)

E.g. [available Amazon UK](https://www.amazon.co.uk/Waveshare-1-8inch-LCD-Module/dp/B077YFTMVT)

#### Load cells for weight sensing the coffee pot

E.g. [available Amazon UK](https://www.amazon.co.uk/gp/product/B07GRGT3C3)

#### HX711 A/D converter for load cells

[HX711 Data sheet](hx711/hx711_english.pdf)

