from classes.config import Config
c = Config()

from classes.display import Display
d = Display(c.settings,True) # Emulate
d.begin()

from classes.display import Pot
p = Pot(d.LCD)
p.begin()

