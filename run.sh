#!/bin/bash

echo $(date) '[info] cambridge_coffee_pot/run.sh starting...' >>/home/pi/cambridge_coffee_pot.log

cd /home/pi/cambridge_coffee_pot/code

source /home/pi/cambridge_coffee_pot_venv/bin/activate

# echo $(date) '[warning] cambridge_coffee_pot/run.sh disabled'

# Data readings collection version:
#python3 main.py config/sensor_debug.json

# Normal version
python3 main.py >/home/pi/cambridge_coffee_pot_run.log 2>/home/pi/cambridge_coffee_pot_run.err

echo $(date) '[info] cambridge_coffee_pot/run.sh completed' >>/home/pi/cambridge_coffee_pot.log

