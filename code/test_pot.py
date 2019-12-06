from classes.config import Config
c = Config()

from classes.display import Display
d = Display(c.settings,True) # Emulate
d.begin()

from classes.display import Pot
p = Pot(d.LCD, x=10, y=10, w=38, h=100, settings=c.settings)
p.begin()

