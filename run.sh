#!/bin/bash

echo $(date) '[info] cambridge_coffee_pot/run.sh starting...'

cd /home/pi/cambridge_coffee_pot/code

# echo $(date) '[warning] cambridge_coffee_pot/run.sh disabled'
python3 sensor.py

echo $(date) '[info] cambridge_coffee_pot/run.sh completed'

