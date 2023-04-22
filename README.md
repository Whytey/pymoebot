# pymoebot

A Python library intended to monitor (and control?) the [MoeBot](https://moebot.com.au/) robotic lawn mowers.

* MoeBot are controllable over WiFi via the Tuya protocol, using the Tuya apps on your Apple/Android device.
* Tested using an S5 model of MoeBot (which is identical to an S10 (and S20??) apart from battery size).
* A number of other Robot Mowers appear to be physically identical, though it is unconfirmed if they work (or even support WiFi control):
  * [JIUDU DM2](https://www.youtube.com/watch?v=-xFCVvPeR6c)
  * [AYI DRM3 600i](https://www.youtube.com/watch?v=M9zYBOIgAg4)
  * [Hyundai HYRM1000](https://www.youtube.com/watch?v=kNKszbw8_g8)
  * [Gtech RLM50](https://www.youtube.com/watch?v=t7GGCzNhHKc)
  * [Sømløs G1/G1s](https://www.youtube.com/watch?v=LDyRpMmVYTs)
* This library provides a MoeBot facade to the [tinytuya](https://github.com/jasonacox/tinytuya) library.
* The ultimate intent is to have a library that can then be used within [Home-Assistant](http://www.home-assistant.io)

## Goals

- [x] Monitor the MoeBot 
- [ ] Control the MoeBot
- [ ] Integrate into Home-Assistant stand-alone. 
- [ ] If possible, merge into the Home-Assistant Tuya integration

## History

It was originally intended to utilise the official `tuya-iot-python-sdk` library but that provided minimal support for the MoeBot.  Instead, this library now uses local communication with the MoeBot via the `tinytuya` library.  This does require a little bit of pre-work to identify the `LOCAL_KEY` for the device so that we can communicate with it.   

Regardless of chosen library we are required to have configured a Tuya Cloud project, follow these [instructions](https://github.com/jasonacox/tinytuya#setup-wizard---getting-local-keys) 

## Using pymoebot
> **_NOTE:_**  The MoeBot needs to have been activated by adding it to the Tuya/SmartLife app first.

In it's most simplistic use, get an instance of `MoeBot` and query its status.

```python
from pymoebot import MoeBot

moebot = MoeBot('DEVICE_ID', 'IP', 'LOCAL_KEY')
print("Battery level: %s%" % moebot.battery)
```

See the [examples](https://github.com/Whytey/pymoebot/tree/main/examples) for full examples of usage.

# Communicating with the MoeBot

`tinytuya` have done all the hard work of communicating with the MoeBot.  It is worth sharing my understanding of the specifics about the MoeBot though, since I have made some assumptions and peer-review may be able to identify issues.

The MoeBot (like all other Tuya devices) communicates by way of Tuya Data Points (DPS).  Some of these are declared when the mower is queried.  Others are provided unsolicited.

```python
import tinytuya

d = tinytuya.Device('DEVICEID', 'DEVICEIP', 'DEVICEKEY')
d.set_version(3.3)
print(d.status())
```
Will result in:

```
{'dps': {'6': 100, '101': 'STANDBY', '102': 0, '103': 'MOWER_LEAN', '104': True, '105': 3, '106': 1111, '114': 'AutoMode'}}
```

## Tuya Data Points
| DPS  | Read/Write | Values                                                                                                                                                                 | Comment                                                                                 |
|------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 6    | r/w       | 0-100                                                                                                                                                                  | 'Battery'                                                                               |
| 101  | r         | <ul><li>STANDBY</li><li>MOWING</li><li>CHARGING</li><li>EMERGENCY</li><li>LOCKED</li><li>PAUSED</li><li>PARK</li><li>CHARGING_WITH_TASK_SUSPEND</li><li>FIXED_MOWING</li><li>ERROR</li></ul> | 'Machine Status' Provides state - can't seem to command state using this                |
| 102  | r         | 0                                                                                                                                                                      | 'Machine error'                                                                         |
| 103  | r         | <ul><li>MOWER_LEAN</li><li>MOWER_EMERGENCY</li><li>MOWER_UI_LOCKED</li><li>NO_LOOP_SIGNAL</li><li>BATTERY_NOT_ENOUGH</li><ul>                                                                                            | 'Machine warning' Provides sub-states for when the mower is in EMERGENCY                |
| 104  | r/w       | True/False                                                                                                                                                             | 'Rain mode' Should we work in the rain?                                                 |
| 105  | r/w       | 1-99                                                                                                                                                                   | 'work time' How many hours to run for when started manually                             |
| 106  | r/?       | 1111                                                                                                                                                                   | 'machine password'                                                                      |
| 107  | w         | True/False                                                                                                                                                             | 'Clear machine appointment' results in a DPS 110 response                               |
| 108  | w         | True/False                                                                                                                                                             | 'Query machine reservation' results in a DPS 110 response                               | 
| 109  | w         | True/False                                                                                                                                                             | 'query partition parameters' results in a DPS 113 response                              |
| 110  | r/w       | [byte data]                                                                                                                                                            | 'Report machine Reservation'                                                            |
| 111  | r/?      | [byte data]                                                                                                                                                            | 'error log'                                                                             |
| 112  | r/w       | [byte data]                                                                                                                                                            | 'work log' Report of mower working time after work has completed, contains last 10 logs |
| 113  | r/w       | [byte data]                                                                                                                                                            | 'Partition parameters' specifies the zone mowing configuration                          |
| 114  | r/?       | AutoMode/??                                                                                                                                                            | 'WorkMode'                                                                              |
| 115  | w         | <ul><li>StartMowing</li><li>StartFixedMowing</li><li>PauseWork</li><li>CancelWork</li><li>StartReturnStation</li><ul>                                                  | 'Machine Control CMD' used to change mower state                                        |

## State Model

### Main States
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

### EMERGENCY States
The following appear to be sub-states for when the mower is in EMERGENCY state.  They are signified by a '103' DPS.

* MOWER_LEAN
* MOWER_EMERGENCY
* MOWER_UI_LOCKED
* PLACE_INSIDE_STATION
* BATTERY_NOT_ENOUGH
