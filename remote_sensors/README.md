# Remote sensors connecting to the Sensor Node

[A list of smart devices that can be flashed with Tasmota](https://blakadder.github.io/templates)

[Raspberry Pi as WiFi Access Point for remote sensor backhaul](pi_ap/README.md)

[Raspberry Pi receive the remote sensor data via MQTT](pi_mqtt/README.md)

[Tasmota firmware installation and configuration](tasmota/README.md)

## Templates for UK energy monitoring plugs

Anoopsyche JH-G01B1 `{"NAME":"JH-G01B1","GPIO":[0,145,0,146,0,0,0,0,17,56,21,0,0],"FLAG":0,"BASE":41}`

Anoopsyche UK1 `{"NAME":"UK1D","GPIO":[0,17,0,0,133,132,0,0,130,52,21,0,0],"FLAG":0,"BASE":6}`

Avatar AWP14H `{"NAME":"Avatar UK 10A","GPIO":[0,0,56,0,0,134,0,0,131,17,132,21,0],"FLAG":0,"BASE":45}`

2Nice UP111 `{"NAME":"2NICE UP111","GPIO":[0,52,0,17,134,132,0,0,131,157,21,0,0],"FLAG":0,"BASE":18}`

Gosund UP111 `{"NAME":"Gosund UP111","GPIO":[0,52,0,17,134,132,0,0,131,157,21,0,0],"FLAG":0,"BASE":18}`

Koogeek KLUP1 `{"NAME":"Koogeek-KLUP1","GPIO":[0,0,0,17,134,132,0,0,131,56,21,0,0],"FLAG":0,"BASE":18}`

Aoycocr U3S `{"NAME":"Aoycocr U3S","GPIO":[56,255,57,255,0,134,0,0,131,17,132,21,0],"FLAG":0,"BASE":45}`

## Anoopsyche JH-G01B1 smart plug

![Anoopsyche smart plug](Anoopsyche_JH-G01B1/JH-G01B1.png)

![open](Anoopsyche_JH-G01B1/open.jpg)
![top](Anoopsyche_JH-G01B1/circuit_top.jpg)
![bottom](Anoopsyche_JH-G01B1/circuit_bottom.jpg)
![side](Anoopsyche_JH-G01B1/circuit_side.jpg)

### Tasmota JH-G01B1 Config Template
```
{"NAME":"JH-G01B1","GPIO":[0,145,0,146,0,0,0,0,17,56,21,0,0],"FLAG":0,"BASE":41}
```

## Avatar (aka Aisirer) AWP14H smart plug

![Avatar AWP14H smart plug](Avatar_AWP14H/AWP14H.png)

### Tasmota Config Template
```
{"NAME":"Avatar UK 10A","GPIO":[0,0,56,0,0,134,0,0,131,17,132,21,0],"FLAG":0,"BASE":45}
```
