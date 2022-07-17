import logging

import tinytuya

_log = logging.getLogger("pymoebot")


class MoeBot:
    def __init__(self, device_id: str, device_ip: str, local_key: str) -> None:
        self.__id = device_id
        self.__ip = device_ip
        self.__key = local_key

        self.__device = tinytuya.Device(self.__id, self.__ip, self.__key)
        self.__device.set_version(3.3)
        self.__device.set_socketPersistent(True)

        self.__listeners = []

        self.__battery = None
        self.__state = None
        self.__emergency_state = None
        self.__mow_in_rain = None
        self.__mow_time = None

        _log.error("test error")

        # payload = self.__device.status()
        # if not self.__parse_payload(payload):
        #     raise MoeBotConnectionError()

    def __parse_payload(self, data) -> bool:
        if 'Err' in data or 'dps' not in data:
            _log.error("Error from device: %r" % data)
            return False
        
        dps = data['dps']
        if '6' in dps:
            self.__battery = dps['6']
        if '101' in dps:
            self.__state = dps['101']
        if '103' in dps:
            self.__emergency_state = dps['103']
        if '104' in dps:
            self.__mow_in_rain = dps['104']
        if '105' in dps:
            self.__mow_time = dps['105']
        
        return True

    async def listen(self):
        _log.debug(" > Send Request for Status < ")
        payload = self.__device.generate_payload(tinytuya.DP_QUERY)
        self.__device.send(payload)

        _log.debug(" > Begin Monitor Loop <")
        while True:
            # See if any data is available
            data = self.__device.receive()
            if data is not None:
                _log.debug("Received Payload: %r", data, exc_info=1)

                self.__parse_payload(data)
                for listener in self.__listeners:
                    listener(data)

            # Send keepalive heartbeat
            payload = self.__device.generate_payload(tinytuya.HEART_BEAT)
            self.__device.send(payload)

    def add_listener(self, listener) -> None:
        self.__listeners.append(listener)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def mow_time(self) -> int:
        return self.__mow_time

    @mow_time.setter
    def mow_time(self, mow_time: int):
        self.__device.set_value('105', mow_time)

    @property
    def mow_in_rain(self) -> bool:
        return self.mow_in_rain

    @mow_in_rain.setter
    def mow_in_rain(self, mow_in_rain: bool):
        self.__device.set_value('104', mow_in_rain)

    @property
    def battery(self) -> int:
        return self.__battery

    @property
    def state(self) -> None:
        return self.__state

    def __repr__(self) -> str:
        return "[MoeBot - {id: %s, state: %s, battery: %s}]" % (self.id, self.__state, self.__battery)


class MoeBotConnectionError(Exception):
    pass