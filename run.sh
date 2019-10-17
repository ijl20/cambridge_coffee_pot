#!/bin/bash

echo $(date) '[info] cambridge_coffee_pot/run.sh starting...'

cd /home/pi/cambridge_coffee_pot/code

python3 sensor.py

echo $(date) '[info] cambridge_coffee_pot/run.sh completed'

