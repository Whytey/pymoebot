# pymoebot

A Python library intended to monitor (and control?) the [MoeBot](https://moebot.com.au/) robotic lawn mowers.

* MoeBot are controllable over WiFi via the Tuya protocol, using the Tuya apps on your Apple/Android device.
* Tested using an S5 model of MoeBot (which is identical to an S10 (and S20??) apart from battery size).
* A number of other Robot Mowers appear to be identical; [JIUDU](https://www.youtube.com/watch?v=-xFCVvPeR6c), [AYI](https://www.youtube.com/watch?v=M9zYBOIgAg4)
* This library provides a MoeBot facade to the [tinytuya](https://github.com/jasonacox/tinytuya) library.
* The ultimate intent is to have a library that can then be used within [Home-Assistant](http://www.home-assistant.io)

## Goals

1. Monitor the MoeBot
2. Control the MoeBot
3. Integrate into Home-Assistant stand-alone.
4. If possible, merge into the Home-Assistant Tuya integration

## History

It was originally intended to utilise the official `tuya-iot-python-sdk` library but that provided minimal support for the MoeBot.  Instead, this library now uses local communication with the MoeBot via the `tinytuya` library.  This does require a little bit of pre-work to identify the `LOCAL_KEY` for the device so that we can communicate with it.   Both libraries require us to have configured a Tuya Cloud project, follow these [instructions](https://github.com/jasonacox/tinytuya#setup-wizard---getting-local-keys) 

## Using pymoebot
In it's most simplistic use, get an instance of `MoeBot` and query its status.

```python
from pymoebot import MoeBot

moebot = MoeBot('DEVICE_ID', 'IP', 'LOCAL_KEY')
print("Battery level: %s%" % moebot.battery)
```

See the [examples](https://github.com/Whytey/pymoebot/tree/main/examples) for full examples of usage.

## Communicating with the MoeBot

`tinytuya` have done all the hard work of communicating with the MoeBot.  It is worth sharing my understanding of the specifics about the MoeBot though, since I have made some assumptions and peer-review may be able to identify issues.

The MoeBot (like all other Tuya devices) communicates by way of Tuya Data Points (DPS).  Some of these are declared when the mower is queried.  Others are provided unsolicited.

```python
import tinytuya

d = tinytuya.Device('DEVICEID', 'DEVICEIP', 'DEVICEKEY')
d.set_version(3.3)
d.status()
{'dps': {'6': 100, '101': 'STANDBY', '102': 0, '103': 'MOWER_LEAN', '104': True, '105': 3, '106': 1111, '114': 'AutoMode'}}
```

| DPS | Read/Write | Values                                                                                                                   | Comment                                                 |
|-----|------------|--------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| 6   | r/w        | 0-100                                                                                                                    | Battery                                                 |
| 101 | r/?        | STANDBY MOWING/CHARGING/EMERGENCY/LOCKED/<br/>PAUSED/PARK/CHARGING_WITH_TASK_SUSPEND/FIXED_MOWING                        | Provides state - can't seem to command state using this |
| 102 | ??         | ??                                                                                                                       | Unknown                                                 |
| 103 | r/?        | MOWER_LEAN/MOWER_EMERGENCY/MOWER_UI_LOCKED/                                                                              | Provides sub-states for when the mower is in EMERGENCY  |
| 104 | r/w        | True/False                                                                                                               | Should we work in the rain?                             |
| 105 | r/w        | 1-12                                                                                                                     | How many hours to run for when started manually         |
| 106 | r/?        | 1111/??                                                                                                                  | Unknown                                                 |
| 107 | w          | True/False                                                                                                               | Unknown but results in a DPS 110 response               |
| 108 | w          | True/False                                                                                                               | Unknown but results in a DPS 110 response               | 
| 109 | w          | True/False                                                                                                               | Unknown but results in a DPS 113 response               |
| 110 | -          | AIiIiIgBiIiIiAKIiIiIA4iIiIgEiIiIiAWIiIiIBoiIiIg=                                                                         | Unknown                                                 |
| 111 | -          | Ylxw+RRiXG/nFGJVvhsUYlW9/wJiVb30AmJJefACYkl5zAJiSXm/AmJJWowCAAAAAAA=                                                     | Unknown                                                 |
| 112 | -          | YoJb5wAAKK4BYoDkWAAAQOUBYn+SygAABUABYn5JAwAADcsBYn5ITQAAAEYBYn5IEQAAADwBYn5H4QAAADwBYn5HtQAAADwBYn5HigAAADwBYn5HYAAAADwB | Report of mower working time after work has completed   |
| 113 | -          | AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==                                                                                     | Unknown                                                 |
| 114 | r/?        | AutoMode/??                                                                                                              | Unknown                                                 |
# State Model

## Main States
The following are the declared states of the MoeBot seen so far.  They are signified by a '101' DPS.

* CHARGING
* EMERGENCY - the emergency stop button has been pressed (or the device has been tipped/picked up).
* LOCKED - the device is locked and the PIN is required to do anything.
* PAUSED - the mowing session has been paused.
* MOWING
* CHARGING_WITH_TASK_SUSPEND - currently charging but will go back out to mow.
* STANDBY - the mower is not mowing and is charged.  May or may not be docked.
* PARK - on the way back to the charging dock.
* FIXED_MOWING - working in a spiral pattern.

## EMERGENCY States
The following appear to be sub-states for when the mower is in EMERGENCY state.  They are signified by a '103' DPS.

* MOWER_LEAN
* MOWER_EMERGENCY
* MOWER_UI_LOCKED
* PLACE_INSIDE_STATION

# API References
### `/v1.0/iot-03/categories/gcj/functions`
```
[
    {
        "code": "mode",
        "desc": "mode",
        "name": "mode",
        "type": "Enum",
        "values": '{"range":["standby","random","smart","wall_follow","spiral","chargego"]}',
    },
    {
        "code": "battery_percentage",
        "desc": "battery percentage",
        "name": "battery percentage",
        "type": "Integer",
        "values": '{"unit":"%","min":0,"max":100,"scale":0,"step":1}',
    },
    {
        "code": "switch_go",
        "desc": "switch go",
        "name": "switch go",
        "type": "Boolean",
        "values": "{}",
    },
    {
        "code": "direction_control",
        "desc": "direction control",
        "name": "direction control",
        "type": "Enum",
        "values": '{"range":["forward","backward","turn_left","turn_right","stop"]}',
    },
    {
        "code": "switch",
        "desc": "switch",
        "name": "switch",
        "type": "Boolean",
        "values": "{}",
    },
]
```