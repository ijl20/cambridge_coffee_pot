<img align="right" src="images/cambridge_logo.png"/>

# Cambridge Coffee Pot

Back in the day (1991) we had this coffee pot with a low-res monochrome camera connected to
a frame-grabber and a server in the Computer Laboratory, then in the Austin Building in central
Cambridge.  We could type the command ```xcoffee``` on our workstations and decide whether to make
the arduous trip around to the coffee machine or lurk in our offices until some worthy colleague had
made a fresh pot of coffee. When the world-wide-web first became a thing we connected the frame grabber
to a web server and were surprised how many people around the world wanted to see a 'webcam' (the word wasn't
yet invented) and the rest is history (see [Trojan Room coffee pot](https://en.wikipedia.org/wiki/Trojan_Room_coffee_pot)).

![Original Trojan Room coffee pot image](images/Trojan_Room_coffee_pot_xcoffee.png)

Well, here we are ~30 years later in a somewhat shinier modern Computer Laboratory out at West Cambridge, but
the endemic coffee dependency remains a central theme, with our kitchen looking like this:

![Current Netos coffee pot image 2019-10-08](images/kitchen.jpg)

So the question is, should we have a **new** coffee sensor and if so what would it look like in 2019 vs 1991?


## The concept

Build a sensor set that measures and transmits in real-time the coffee-making
and consuming events happening on the Computer Lab Cambridge Coffee Pot.

This is actually monitoring the direct descendant of the original
Cambridge [Trojan Room coffee pot](https://en.wikipedia.org/wiki/Trojan_Room_coffee_pot)
from 1991 to 2001.

![whiteboard sketch Ian Lewis and Brian Jones](images/whiteboard_design.jpg)

## Sample data

The sensor will take weight measurements as in the sample data illustrated below which was
collected using the first prototype.

The sensor will recognize events
such as a fresh pot of coffee being placed, a cup being taken, and the pot becoming empty.
 The objective is that these events are communicated
to the server with the minimum latency while the periodic reporting of the weight (e.g. once a
minute or so) is primarily a 'watchdog' message confirming the coffee pot is working.

![data chart of weight load with time for full coffe pot plus pouring 1 cup](data/sample_weights_fill_plus_1_cup.png)

The pot weighs ~0.5 Kg, and when full holds 2Kg of coffee. Each cup taken is ~0.25Kg.

It was unexpected that the press on the plunger to pour a cup of coffee could result in
combined downward weight >10Kg.

## Prototype

2019-10-09

![William Gates Building Ian Lewis office FE11 sensor prototype](images/prototype.jpg)

Note in this first prototype I'm using a *single* hx711 to A/D convert both load cells, as
the hx711 has two channels (A & B) which are not equally accurate but both good enough for
our application. But when reading both A/D values on the Pi from channel A followed by channel B
a ~half second latency was required between the two readings as the hx711 is clearly multiplexing some
of its circuitry between the two channels.

### Version with 2 x 5Kg load cells and 2 A/D converters, with a prototype housing.

2019-10-04

![2 load cells](images/two_load_cells.jpg)

In this image you can see I moved the two load cells onto two separate hx711 A/D converters
and used the A channel of each. This reduced the single read time of both sensors to a few milliseconds. The
A/D sample rate defined in the hx711's is defaulted to 10Hz (the alternative is 80Hz) so there is no point in
repeating readings within 100ms.

Here we hit an engineering problem. The weighing platform was reasonable stable 'fore and aft' i.e.
along the axis the pot is placed on the sensor (as was the intention and the mountings for the two
load cells were aligned this way). However, when the plunger is pressed
the tilting forces *from side to side* were larger than expected and the weighing platform felt too fragile
on that axis to survive long in production use. The considered solutions were some sliding pillar arrangement
to keep the weighing platform from rocking, or the use of four load cells. We went with the latter.

To keep the height of the housing as small as practicable the electronics are placed in a sealed separate area
adjacent to the load cells (as opposed to beneath them). This gives the overall housing the approximate plan
dimensions of an A4 sheet of paper. The 'landscape' arrangement of this sensor made poor use of the space available
in the kitchen so in the next version a 'portrait' arrangement was used.

### Next version with 4 x 5Kg load cells

2019-10-06

![4 load cells](images/four_load_cells.jpg)

In addition to the four load cells, this prototype uses 4 x hx711 A/D converters to reduce latency in reading
as with two.

### Adding the LCD display

2019-10-06

The 'portrait' arrangement conflicts with the simple solution of putting the LCD display to the left
or right of the load area, as was planned with the 'landscape' design.

The solution was to use transparent acrylic for the weighing platform and mount the LCD *under*
the front left corner of the weighing platform.

## Real-time events

Embedded in the coffee pot sensor are two load cells that measure the weight of the pot.

In the data-sensing business, everybody, and I mean everybody, assumes the sensor design is finished
after the first
few lines of code are written that actually manages to read the parameter being measured and send the results.
This is understandable as often they will have spent weeks or months just trying to get the measurement sensor
to actually work reliably.

The effect of this is you end up with a 'weight sensor' that either has a built in period for repeatedly
sending its reading, or it can be 'polled' by a server somewhere that periodically asks for its reading. Either
way you end up with a sensor that doesn't really care about the thing it's measuring, and neither does the server,
 so long as the data flow adheres to the once-a-minute (or whatever) regular schedule.

Maybe someone comes along and asks for the data with less system-related latency. The sensor / system developer
will always, and I mean always, respond with one of two answers: (1) you don't need the data more quickly,
or (2) shall I send the data twice as 'fast' (i.e. every 30 seconds).

The truth is the required 'timeliness' (or acceptable latency) of the reading depends considerably on the
state of the 'thing' being measured.  E.g. A traffic speed sensor on a highway that
sends the prevailing traffic speed once a minute is better than no sensor, but there
is no good reason it would send the readings "72,75,71,69,0" at
regular intervals. Hopefully that last reading of ZERO could be sent within a millisecond
of being measured, rather the possibly waiting 59 seconds
to send it as a regular update. And a design that simply sends the measured speeds *every* millisecond is pretty dumb.

This issue regarding the timeliness of sensor data is pervasive, particularly in urban and in-building sensor systems.

Our coffee pot will connect to our existing real-time Intelligent City Platform (which itself can process
incoming events without introducing system-related polling latencies) and will
* send the weight periodically, say once per five minutes - this is best thought of as a 'watchdog' which
happens to carry a useful payload.
* recognize the following events and transmit them to the platform as soon as they are recognized:
    * POT_REMOVED - the pot appears not to be present
    * POT_NEW - freshly made coffee seems to have appeared
    * POT_POURED - a cup was poured
    * POT_EMPTY - pot appears to contain no coffee
    * COFFEE_GROUND - by also monitoring coffee grinding machine (with a microphone), it seems coffee has been ground.

## Visualizing the data

This is an open question at the moment. The original coffee pot presented the data as a 128x128px monochrome
image and it was left to the viewer how to interpret it, combined with an implicit assumption the user would
issue the ```xcoffee``` command at the time they were interested in the coffee.

The new design can assume the permanent connection of web-based displays (in addition to the 'user request'
model) and we will consider (i.e. measure) the latency in the system reporting a fresh pot of coffee.

It has been suggested that any self-respecting coffee machine in 2019 would have a Twitter account. [[ref]](#ref_1)


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

## CPU

For this one-off experimental sensor we used a Raspberry Pi 3B+, using the GPIO pins to
connect the LCD display (via SPI) and the two load cell A/D converters (each needing +Vcc, GND and two data
pins)

![Pi 3 B+ GPIO pinout with LCD and 4 load cells](images/pi_3_gpio_4_load_cells.png)


## LCD Display - Waveshare 1.8inch color LCD module

We interact with this via the st7735_ijl20 library `code/st7735_ijl20/st7735.py`

![1.8 inch 128x160 lcd display](images/lcd_1.8in_128x160.jpg)

[Online info](https://www.waveshare.com/wiki/1.8inch_LCD_Module)

E.g. [available Amazon UK](https://www.amazon.co.uk/Waveshare-1-8inch-LCD-Module/dp/B077YFTMVT)

[LCD Module Schematic (pdf)](LCD_1in8/1.8inch-LCD-Module-Schematic.pdf)

[LCD Module user manual (pdf)](LCD_1in8/1.8inch_LCD_Module_User_Manual_EN.pdf)

[ST7735 data sheet (pdf)](LCD_1in8/ST7735S_V1.1_20111121.pdf)

## Load cells for weight sensing the coffee pot

Two 5Kg load cells connected via two HX711 A/D converters.

We connect with the A/D converters via the `code/hx711_ijl20/hx711.py` library

![load cell](images/load_cell.jpg)

E.g. [available Amazon UK](https://www.amazon.co.uk/gp/product/B07GRGT3C3)

[HX711 Data sheet](hx711/hx711_english.pdf)

## The web client

The Cambridge Intelligent City Platform is used to receive the real-time data (periodic weight readings and low-latency
events) from the sensor and also provide some user-appropriate display derived from this data. The information
sent to the Platform for a sample day is visualized below (the 'event' pattern matching in the
sensor is first-cut prototype):

![platform watchdog/events chart](images/2019-12-11_server_data.png)

At this scale the periodic weight readings look detailed but it is *important* to note these are sent on a
regular 2 minute interval and for real-time purposes provide a potential 2 minute latency to the actual
state of the sensor. 

In contrast the events (which include the current weight) are sent as soon
as the event pattern is recognized (e.g. within a second of a cup being poured). The key point is that
the 'events' latency is dominated by the characteristics of the behaviour being monitored 
rather than some artificial time constant (like a polling interval) embedded in the software.
For example a 'cup poured' event requires time to recognize
potentially multiple presses on the pot plunger as a single 'cup poured' event.

This web client uses the Intelligent City Platform [rtclient](https://github.com/ijl20/rtclient) as a starting 
framework.

Here's an image of the client during development 2019-12-13:

![xcoffee dev image](images/xcoffee_dev.png)

## References

<a id="ref_1">[1]</a> Heidi Howard, in conversation around the Coffee Pot, Cambridge Computer Lab, 2019-10-30
