# Tasmota smart plug firmware

This is the 'replacement' open-source firmware compatible with generic ESP8266 wifi microcontrollers.

After the firmware is installed (see tuya-convert below) the smart device will boot in Access Point mode
and provide an open wifi SSID 'tasmota-XXXX' you can connect to from any device (e.g. smartphone) and 
browse to the address '192.168.4.1' where the device Tasmota configuration page will be shown.

[Docs homepage](https://tasmota.github.io/docs/#/Home)

## Installing Tasmota via tuya-convert

This is the software you can use to install the Tasmota firmware over the wifi connection. It relies
upon a vulnerability in the common 'Tuya' smart device firmware commonly pre-installed.

This is likely to be most straightforward if you use a Raspberry Pi (e.g. 3B+) as the tuya-convert
'host'. Note that tuya-convert significantly re-configures the WiFi interface of the Pi (to provide an
access point for the smart device to connect to) which will leave it unusable for normal client use afterwards
so it is worth creating a microSD Raspian build dedicated to this purpose.

These instructions will refer to three devices:
1. **FLASH PI** : the Raspberry Pi you are using to run the tuya-convert software.
2. **SMART DEVICE** : the smartplug or whatever you are installing Tasmota onto.
3. **PHONE** : your smartphone or other Wifi enabled device you can use to connect to a wifi network and browse the web.

On the **FLASH PI**:

Git clone the tuya-convert software from [Github](https://github.com/ct-Open-Source/tuya-convert), i.e.
```
git clone https://github.com/ct-Open-Source/tuya-convert
cd tuya-convert
```

Install the required dependencies with:
```
./install_prereq.sh
```
Fix any problems you noticed during the above, perhaps with a reboot.

Run the over-the-air firmware flash program:
```
./start_flash.sh
```

The Flash Pi will broadcast a new wifi SSID 'vtrust-flash' and pause at a prompt:
```
...hit Enter to flash your device
```
Do NOT hit Enter yet.

On the **PHONE**:

Open up your wifi settings, give it a few seconds to refresh, and connect to the network `vtrust-flash`. The phone
is not needed for anything else, just to successfully connect to the ssid before the smart device will.

The phone will complain about 'no internet' but don't worry, the phone has done its required job.

If the phone does not show the `vtrust-flash` wifi network then `start_flash.sh` hasn't initialized properly,
probably becuase the pre-requisites are not installed properly, so reboot at start again from scratch.

If the phone can see the `vtrust-flash` network but doesn't connect on first attempt (this is common) then try
again on the phone. You can also try stopping and restarting `./start_flash.sh` on the Flash Pi.

From here we're assuming you *did* connect the phone to the `vtrust-flash` wifi SSID.

On the **SMART DEVICE** :

Plug the smart device into power, wait for it to boot up.

Press and hold the button on the device for >5 seconds to put the device into 'Pairing mode'. Most smartplugs work this
way but if you have something more exotic there should be instructions how to put the device into 'Pairing mode'.

The LED on the smart device should now be flashing, and will remain in 'Pairing mode' until some timeout, e.g. 30 seconds,
during which time you need to kick off the flash download from the Flash Pi.

On the **Flash Pi**:

The LED on the smart device should be flashing, indicating it is ready to download the firmare.

Hit 'Enter' at the `./start_flash.sh` prompt.

`./start_flash.sh` will display a sequence of messages and download bootloader firmware to the smart device.

If `./start_flash.sh` gets stuck in a loop saying '...retrying' then the connection across the `vtrust-flash`
wifi network hasn't been successful. Let the '...retrying' loop complete (it will time out after a number of tries)
and have another go at connecting your phone to the `vtrust-flash` network. If this fails then restart `./start_flash.sh`
and do the whole sequence again

When the bootloader software is successfully installed the smart device will reboot.

At this point we're assuming the `./start_flash.sh` has successfully installed the bootloader firmware, and is giving a new
prompt:
```
... choose Firmware 1), 2) etc
```
Hit the number key corresponding to the `tasmota.bin` firmware. `./start_flash.sh` will immediately respond with:
```
... "y" to confirm
```

Hit the "y" key and `./start_flash.sh` will install the `tasmota.bin` software onto the smart device, followed by the prompt:
```
...Have Fun!
hit Enter to flash another device
```

At this point, if you have only one smart device to flash, you can quit `./start_flash.sh`. If you have other devices to flash it
is work keeping `./start_flash.sh` running because it will maintain the existing `vtrust-flash` wifi network and you no longer need
to bootstrap the network into life via your phone.

The smart device will reboot into the Tasmota firmware, and come up as a WiFi access point on a new SSID 'tasmota-1234' (or other number).

On your **PHONE**:

Again review your available wifi networks, and join 'tasmota-1234' (or whatever). The phone will complain about 'No Internet' but
this is normal.

Open the web browser on the phone and browser `192.168.4.1`. You should see the Tasmota device homepage. If so, congratulations.

This is where you tell the smart device the actual WiFi network/password you would like it to connect to (AP1). You can also tell it
a *second* Wifi SSID/pwd to use as a fallback (e.g. 'backupnet/backupnet'). Note at this point **it is possible to brick the device**
if you give it wrong WiFi credentials as you will then not be able to contact the device in any way.

After setting the WiFi credentials check them again.  And again. Then click 'SAVE' and the smart device will reboot.

## Configuring Tasmota on the Smart Device

If you followed the instructions above, the smart device is now rebooted and connected to the Wifi network with a random IP
address you are going to need to find, either by looking at the DHCP client list on the router or by using a network scanning tool
such as `nmap`.

The Cambridge `sensor_node` design uses a Raspberry Pi as an Access Point to deliver a dedicated sensor WiFi network. In this
example the sensor node is called `csn-node-test` on sensor network address `192.168.75.1`, and providing an MQTT server on
port `1883`. The username/password for the MQTT server are `csn-node-test`/`csn-node-test` and the smart device will publish all
data messages to topics starting `csn-node-test-a/...`. The Cambridge sensor node Raspberry Pi also provides a time NTP service.

In this example the smart devices has booted with an IP address `192.168.75.187`.

### Browse the smart device Tasmota homepage

On a workstation connected to the sensor WiFi network, open the browser to `192.168.75.187`.

### Get the smart device Mac address

Click `Information` on the homepage. Cut-and-paste the last 6 digits of the Mac address shown on the page e.g. "40:A3:77".

You will use this to customize the name of the smart device, and can usefully write the digits onto the actual device.

Now the settings can be put into the device to map the internal sensors and relays to the correct pins of the internal controller.

### Set the smart device config 'template'

From homepage, click `Configuration`, `Configuration Other` and set the following:

`Friendly name`: `csn-node-<Mac>` omitting the Mac colons, i.e. `csn-node-40A377`.

`Template`: cut-and-paste from [the list of available templates](https://blakadder.github.io/templates)

Ensure you click the template `Activate` checkbox.

Click `SAVE` and the smart device will reboot.

After the device has rebooted, the device homepage will refresh and should now show the new 'Friendly Name' at
the top of the page.

A new `Toggle` button should be on the page, and if you click that you should hear the power on/off relay click in your smart device.
If there is no 'Toggle' button on the page you probably forgot to click the `Activate` checkbox so go back and do that.

### Customize the MQTT and related parameters for data sending

On the smart device homepage enter `Configuration`, `Configure MQTT`.

Set settings as below:

`Host`: 192.168.75.1

`Port`: 1883

`Client`: csn-node-test

`Password`: csn-node-test

`Topic`: csn-node-test-a

`Full Topic`: %topic%/%prefix% *(i.e. reverse the default setting)*

These settings will cause the smart device to periodically send sensor data to `csn-node-test-a/tele/SENSOR`.

The %prefix% values are:

`tele`: periodic telemetry data

`stat`: status response data

`cmnd`: command data

The default sensor telemetry reporting period is 5 minutes, and the smart device may initially report the timestamp in the
data as 1970-01-01, probably with the wrong timezone. We will fix that in the next section.

### Using the smart device console to setup time client and adjust telemetry period

On the smart device homepage, click `Console`. Enter the following commands (or enter just the command name to see the current values):

```
TelePeriod 120
PowerDelta 130

ntpServer1 192.168.75.1
ntpServer2 0
ntpServer3 0
Timezone 0
```

The first command sets the regular telemetry reporting period to 2 minutes, while the second says *also* send a telemetry message if the
power reading changes by 30 watts. This PowerDelta setting isn't completely reliable and can have a considerable latency (~8 seconds) but
provides a way of sending an 'event-based' message rather than rely entirely on the periodic telemetry.

The ntpServer<N> commands tell the smart device to get the time from our sensor node, which will also be advertising the time service via DHCP.

The `TimeZone` is a simple offset from UTC that does not adjust for Summer, so it is better to use `0` and treat the value as UTC.

The [full list of commands is online](https://tasmota.github.io/docs/#/Commands)

## Security

These instructions provide a working but insecure open system. 

There are multiple actions that can be taken to improve the security of the Pi and smart devices, for example
the web interface of the smart devices can be protected with a password.
