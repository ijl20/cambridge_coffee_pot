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

This is where you tell the smart device the actual WiFi network/password you would like it to connect to (AP1). You can tell it
a *second* Wifi SSID/pwd to use as a fallback (e.g. 'backupnet/backupnet')
