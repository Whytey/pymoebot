# py-moebot

A Python library intended to monitor (and control?) the MoeBot (https://moebot.com.au/) robotic lawn mowers.

* MoeBot are controllable over WiFi via the Tuya protocol.
* Tested using a MoeBot S5 (which is identical to an S10 (and S20??) apart from battery size).
* A number of other Robot Mowers appear to be identical; JIUDU (https://www.youtube.com/watch?v=-xFCVvPeR6c), AYI (https://www.youtube.com/watch?v=M9zYBOIgAg4)
* Intent is to have a library that can then be used within Home-Assistant

# Goals

1. Monitor the MoeBot
2. Control the MoeBot
3. Integrate into Home-Assistant stand-alone.
4. If possible, merge into the Home-Assistant Tuya integration

# TuyaOpenMQ

The library sniffs the TuyaOpenMQ for messages that provide updates on the MoeBot status.  (It is hoped that these status message may provide insight into the commands that need to be issued to control the mower, via the `TuyaDeviceManager.send_commands()` method).

Status messages all seem to follow the same format:
```
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
`'status': [{'101': 'PAUSED'}]`

### State 103
`'status': [{'103': 'MOWER_LEAN'}]`

### State 112
`'status': [{'112': 'YoJb5wAAKK4BYoDkWAAAQOUBYn+SygAABUABYn5JAwAADcsBYn5ITQAAAEYBYn5IEQAAADwBYn5H4QAAADwBYn5HtQAAADwBYn5HigAAADwBYn5HYAAAADwB'}]`

### Battery Status
`''status': [{'code': 'battery_percentage', 't': '1652686034', '6': 93, 'value': 93}]'`

# State Model

## Main States
The following are the declared states of the MoeBot seen so far.

* CHARGING
* EMERGENCY
* LOCKED
* PAUSED
* CHARGING
* MOWING
* PARK
* CHARGING_WITH_TASK_SUSPEND
* STANDBY
* PARK

## EMERGENCY States
* MOWER_LEAN
* MOWER_EMERGENCY
* MOWER_UI_LOCKED
