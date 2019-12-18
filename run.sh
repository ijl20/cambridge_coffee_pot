#!/bin/bash

echo $(date) '[info] cambridge_coffee_pot/run.sh starting...'

cd /home/pi/cambridge_coffee_pot/code

# echo $(date) '[warning] cambridge_coffee_pot/run.sh disabled'

# Data readings collection version:
#python3 main.py config/sensor_debug.json

# Normal version
python3 main.py

echo $(date) '[info] cambridge_coffee_pot/run.sh completed'

