# py-moebot

A Python library intended to monitor (and control?) the [MoeBot](https://moebot.com.au/) robotic lawn mowers.

* MoeBot are controllable over WiFi via the Tuya protocol, using the Tuya apps on your Apple/Android device.
* Tested using a MoeBot S5 (which is identical to an S10 (and S20??) apart from battery size).
* A number of other Robot Mowers appear to be identical; [JIUDU](https://www.youtube.com/watch?v=-xFCVvPeR6c), [AYI](https://www.youtube.com/watch?v=M9zYBOIgAg4)
* Intent is to have a library that can then be used within [Home-Assistant](http://www.home-assistant.io)

# Goals

1. Monitor the MoeBot
2. Control the MoeBot
3. Integrate into Home-Assistant stand-alone.
4. If possible, merge into the Home-Assistant Tuya integration

# TuyaOpenMQ

The library sniffs the TuyaOpenMQ for messages that provide updates on the MoeBot status.  (It is hoped that these status message may provide insight into the commands that need to be issued to control the mower, via the `TuyaDeviceManager.send_commands()` method).

Status messages all seem to follow the same format:
```python
{
    "data": {
        "dataId": "<UUID of the message>",
        "devId": "<unique device ID / MAC address",
        "productKey": "auojpnb4hpc13ftb",
        "status": [<status data>],
    },
    "protocol": 4,
    "pv": "2.0",
    "sign": "<assumed to be a hash of the 'data' payload?>",
    "t": <UNIX timestamp>,
}
```

### State 101
The MoeBot's state when mowing.

`'status': [{'101': 'PAUSED'}]`

### State 103
Flags an EMERGENCY condition.

`'status': [{'103': 'MOWER_LEAN'}]`

### State 110
Sent together with a State 113 message when is started to rain.

`'status': [{'110': 'AIiIiIgBiIiIiAKIiIiIA4iIiIgEiIiIiAWIiIiIBoiIiIg='}]`

### State 111
Came following a 110 and 113.  Maybe signifies rain end??

`'status': [{'111': 'Ylxw+RRiXG/nFGJVvhsUYlW9/wJiVb30AmJJefACYkl5zAJiSXm/AmJJWowCAAAAAAA='}]`

### State 112
Fairly certain this is logging the time spent working this mowing session.

`'status': [{'112': 'YoJb5wAAKK4BYoDkWAAAQOUBYn+SygAABUABYn5JAwAADcsBYn5ITQAAAEYBYn5IEQAAADwBYn5H4QAAADwBYn5HtQAAADwBYn5HigAAADwBYn5HYAAAADwB'}]`

### State 113
This could be to signal a rain event.

`'status': [{'113': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='}]`

### Battery Status
`''status': [{'code': 'battery_percentage', 't': '1652686034', '6': 93, 'value': 93}]'`

### Other Statuses Seen
The following two messages were seen, that are structured slightly different.  They would appear to signify when a WiFi connection is disconnected or connected.

```python
{
    "data": {
        "bizCode": "offline",
        "bizData": {"time": 1652768419},
        "devId": "<device ID>",
        "productKey": "mvt4l2evgq2l3nkn",
        "ts": 0,
    },
    "protocol": 20,
    "pv": "2.0",
    "sign": "334146791ca446c9a0a3b995ae5a7098",
    "t": 1652768419,
}
{
    "data": {
        "bizCode": "online",
        "bizData": {"time": 1652768422},
        "devId": "<device ID>",
        "productKey": "mvt4l2evgq2l3nkn",
        "ts": 0,
    },
    "protocol": 20,
    "pv": "2.0",
    "sign": "b0d1dc7930df1630387610284eb92479",
    "t": 1652768422,
}

```

# State Model

## Main States
The following are the declared states of the MoeBot seen so far.  They are signified by a '101' message.

* CHARGING
* EMERGENCY - the emergency stop button has been pressed (or the devicehas been tipped/picked up).
* LOCKED - the device is locked and the PIN is required to do anything.
* PAUSED - the mowing session has been paused.
* MOWING
* CHARGING_WITH_TASK_SUSPEND - currently charging but will go back out to mow.
* STANDBY - the mower is not mowing and is charged.  May or may not be docked.
* PARK - on the way back to the charging dock.

## EMERGENCY States
The following appear to be sub-states for when the mower is in EMERGENCY state.  They are signified by a '103' message.

* MOWER_LEAN - may just mean the keypad access flap is lifted?
* MOWER_EMERGENCY
* MOWER_UI_LOCKED
