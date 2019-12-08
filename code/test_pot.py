from classes.config import Config
c = Config()

from classes.display import Display
d = Display(c.settings,True) # Emulate
d.begin()

from classes.display import Pot
p = Pot(d.LCD)
p.begin()

import numpy
import time

def play():
    for i in numpy.arange(0,1,0.01):
        p.update(i)
        time.sleep(0.1)
    for i in numpy.arange(1,0,-0.01):
        p.update(i)
        time.sleep(0.1)
