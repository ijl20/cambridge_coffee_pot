# -------------------------------------------------------------------
#
# Python script to run sensor
#
# -------------------------------------------------------------------

import sys
import time
import asyncio

from classes.config import Config

from classes.sensor_node import SensorNode

from classes.weight_sensor import WeightSensor

from classes.smart_plug import SmartPlug

from classes.sensor_utils import list_to_string

from classes.time_buffer import TimeBuffer

VERSION = "0.80a"


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main code
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------

async def main():

    print("main started with {} arguments {}".format(len(sys.argv), list_to_string(sys.argv)))

    if len(sys.argv) > 1 :
        filename = sys.argv[1]
        config = Config(filename)
    else:
        config = Config()

    config.settings["VERSION"] = VERSION

    event_buffer = TimeBuffer(settings=config.settings)

    sensor_node = SensorNode(settings = config.settings)

    weight_sensor = WeightSensor(config.settings)

    smart_plug_A = SmartPlug(settings=config.settings, sensor_id='smart_plug_A', event_buffer=event_buffer)

    await smart_plug_A.begin()

    sensor_node.begin()

    # Infinite loop until killed, reading weight and sending data
    try:
        while True:
            loop_start_time = time.time()

            #----------------
            # GET READING
            # ---------------

            # get readings from all load cells
            value = weight_sensor.get_value()

            # ---------------
            # PROCESS READING
            # ---------------
            sensor_node.process_sample(time.time(), value)

            loop_time = time.time() - loop_start_time
            if loop_time < 0.1:
                await asyncio.sleep(0.1 - loop_time)

    except (KeyboardInterrupt, SystemExit):
        pass

    # Cleanup and quit
    sensor_node.finish()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    #loop.add_signal_handler(signal.SIGINT, ask_exit)
    #loop.add_signal_handler(signal.SIGTERM, ask_exit)

    loop.run_until_complete(main())
