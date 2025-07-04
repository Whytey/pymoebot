import base64
import logging
import time
from queue import Queue
from threading import Thread, Event

import tinytuya

from .__about__ import __version__

_log = logging.getLogger("pymoebot")
if __debug__:
    _log.addHandler(logging.StreamHandler())
    _log.setLevel(logging.DEBUG)


class ZoneConfig:
    @staticmethod
    def decode(zone_bytes):
        binary = base64.b64decode(zone_bytes)

        zc = ZoneConfig(str(binary[3]), str(binary[4]),
                        str(binary[8]), str(binary[9]),
                        str(binary[13]), str(binary[14]),
                        str(binary[18]), str(binary[19]),
                        str(binary[23]), str(binary[24]))
        return zc

    def __init__(self,
                 z1_distance, z1_ratio,
                 z2_distance, z2_ratio,
                 z3_distance, z3_ratio,
                 z4_distance, z4_ratio,
                 z5_distance, z5_ratio):
        self._z1_distance = z1_distance
        self._z1_ratio = z1_ratio
        self._z2_distance = z2_distance
        self._z2_ratio = z2_ratio
        self._z3_distance = z3_distance
        self._z3_ratio = z3_ratio
        self._z4_distance = z4_distance
        self._z4_ratio = z4_ratio
        self._z5_distance = z5_distance
        self._z5_ratio = z5_ratio

    @property
    def zone1(self) -> (int, int):
        return self._z1_distance, self._z1_ratio

    @property
    def zone2(self) -> (int, int):
        return self._z2_distance, self._z2_ratio

    @property
    def zone3(self) -> (int, int):
        return self._z3_distance, self._z3_ratio

    @property
    def zone4(self) -> (int, int):
        return self._z4_distance, self._z4_ratio

    @property
    def zone5(self) -> (int, int):
        return self._z5_distance, self._z5_ratio

    def encode(self):
        set_binary = [0, 0, 0, self._z1_distance, self._z1_ratio,
                      0, 0, 0, self._z2_distance, self._z2_ratio,
                      0, 0, 0, self._z3_distance, self._z3_ratio,
                      0, 0, 0, self._z4_distance, self._z4_ratio,
                      0, 0, 0, self._z5_distance, self._z5_ratio]
        zone_bytes = base64.b64encode(bytes(set_binary))
        return zone_bytes.decode("ascii")


class MoeBot:

    def __init__(self, device_id: str, device_ip: str, local_key: str) -> None:
        self.__id: str = device_id
        self.__ip: str = device_ip
        self.__key: str = local_key

        self.__device: tinytuya.Device = tinytuya.Device(self.__id, self.__ip, self.__key)

        self.__listeners = []

        self.__battery: int = None
        self.__state = None
        self.__emergency_state = None
        self.__mow_in_rain: bool = None
        self.__mow_time: int = None
        self.__work_mode = None
        self.__online: bool = False
        self.__zones: ZoneConfig = None

        self.__last_update = None
        self.__tuya_version = self.__do_proto_check()
        self.__device.set_version(self.__tuya_version)

        self.__thread: Thread = None
        self.__queue: Queue = Queue(20)
        self.__shutdown: Event = Event()
        self.__shutdown.set()  # The thread should be flagged as not running

    def __do_proto_check(self) -> str:
        versions = [3.4, 3.3]
        for version in versions:
            self.__device.set_version(version)
            result = self.__device.status()
            _log.debug("Set TUYA version to %r and got the following result: %r" % (version, result))
            if self.__parse_payload(result):
                return version

        _log.error("No TUYA version seems to be valid.")
        return 0.0

    def __parse_payload(self, data) -> bool:
        if data is None or 'Err' in data or 'dps' not in data:
            _log.error("Error from device: %r" % data)
            if data is not None and 'Err' in data and data['Err'] == 905:
                self.__online = False
            return False

        self.__online = True
        _log.debug("Parsing data from device: %r" % data)
        dps = data['dps']
        if '6' in dps:
            self.__battery = dps['6']
        if '13' in dps:  #For Koszacy support
            self.__battery = dps['13']
        if '101' in dps:
            self.__state = dps['101']
        if '103' in dps:
            self.__emergency_state = dps['103']
        if '104' in dps:
            self.__mow_in_rain = dps['104']
        if '105' in dps:
            self.__mow_time = dps['105']
        if '113' in dps:
            self.__zones = ZoneConfig.decode(dps['113'])
        if '114' in dps:
            self.__work_mode = dps['114']

        if 't' in data:
            self.__last_update = data['t']

        for listener in self.__listeners:
            listener(data)

        return True

    def __queue_command(self, dps, arg):
        # If we're not listening, we're not processing the queue, so we should do that.
        if self.is_listening:
            # Put the command in the queue
            self.__queue.put((dps, arg))
        else:
            _log.debug("Thread isn't running, so process the command now")
            result = self.__device.set_value(dps, arg)
            self.__parse_payload(result)
        pass

    def __loop(self, send_queue: Queue):
        STATUS_TIMER = 30
        KEEPALIVE_TIMER = 12

        _log.debug("Send an initial request for status")
        self.poll()

        _log.debug("Begin the monitor loop")
        heartbeat_time = time.time() + KEEPALIVE_TIMER
        status_time = time.time() + STATUS_TIMER
        while True:
            if self.__shutdown.is_set():
                _log.debug("Thread has been shutdown, exiting listen loop")
                break
            elif not send_queue.empty():
                command = send_queue.get()
                _log.debug("We have a message in the queue: {}".format(command))
                data = self.__device.set_value(command[0], command[1])
                send_queue.task_done()
            elif status_time and time.time() >= status_time:
                _log.debug("Time to poll for status")
                self.poll()
                status_time = time.time() + STATUS_TIMER
                heartbeat_time = time.time() + KEEPALIVE_TIMER
            elif time.time() >= heartbeat_time:
                _log.debug("Sending a heartbeat")
                data = self.__device.heartbeat(nowait=False)
                heartbeat_time = time.time() + KEEPALIVE_TIMER
            else:
                # no need to send anything, just listen for an asynchronous update
                _log.debug("Just waiting for asynchronous data...")
                data = self.__device.receive()

            if data:
                _log.debug("Received Payload: %r", data)
                if not self.__parse_payload(data):
                    # rate limit retries so we don't hammer the device
                    time.sleep(2)

    def listen(self):
        if self.__shutdown.is_set():
            self.__thread = Thread(target=self.__loop, args=(self.__queue,))
            self.__thread.name = "pymoebot"
            self.__device.set_socketPersistent(True)
            self.__shutdown.clear()
            self.__thread.start()
        else:
            _log.error("Thread was already running")

    def add_listener(self, listener) -> None:
        self.__listeners.append(listener)

    def unlisten(self) -> None:
        _log.debug("Unlistening to MoeBot")
        self.__shutdown.set()
        self.__thread.join()
        self.__queue.join()
        self.__device.set_socketPersistent(False)

    @property
    def is_listening(self) -> bool:
        return not self.__shutdown.is_set()

    def __wait_for_state(self, target_state, timeout=10):
        can_poll = True
        evt = Event()

        def polling_task():
            _log.debug("Waiting for a change to '{}'".format(target_state))
            while can_poll:
                current_state = self.state
                if current_state == target_state:
                    evt.set()
                    break

                _log.debug("Current state '{}' isn't the target state '{}'".format(current_state, target_state))
                time.sleep(0.1)

        t = Thread(target=polling_task)
        t.start()
        evt.wait(timeout=timeout)
        can_poll = False
        t.join()
        _log.info("After waiting, the state is '{}'".format(self.state))

    @property
    def id(self) -> str:
        return self.__id

    @property
    def online(self) -> bool:
        return self.__online

    @property
    def tuya_version(self) -> str:
        return self.__tuya_version

    @property
    def pymoebot_version(self) -> str:
        return __version__

    @property
    def last_update(self) -> int:
        return self.__last_update

    @property
    def mow_time(self) -> int:
        return self.__mow_time

    @mow_time.setter
    def mow_time(self, mow_time: int):
        self.__queue_command(105, mow_time)

    @property
    def mow_in_rain(self) -> bool:
        return self.__mow_in_rain

    @mow_in_rain.setter
    def mow_in_rain(self, mow_in_rain: bool):
        self.__queue_command(104, mow_in_rain)

    @property
    def zones(self) -> ZoneConfig:
        return self.__zones

    @zones.setter
    def zones(self, zone_config: ZoneConfig):
        self.__queue_command(113, zone_config.encode())

    @property
    def battery(self) -> int:
        return self.__battery

    @property
    def state(self) -> str:
        return self.__state

    @property
    def emergency_state(self) -> str:
        return self.__emergency_state

    @property
    def work_mode(self) -> str:
        return self.__work_mode

    def start(self, spiral=False) -> None:
        _log.debug("Attempting to start mowing: %r", self.__state)
        if self.__state in ("STANDBY", "PAUSED", "CHARGING"):
            if self.__state == "PAUSED":
                _log.debug("ContinueWork")
                self.__queue_command(115, "ContinueWork")
            elif not spiral:
                _log.debug("StartMowing")
                self.__queue_command(115, "StartMowing")
            else:
                _log.debug("StartFixedMowing")
                self.__queue_command(115, "StartFixedMowing")
            self.__wait_for_state('MOWING')
        else:
            _log.error("Unable to start due to current state: %r", self.__state)
            raise MoeBotStateException()

    def poll(self):
        result = self.__device.status()
        self.__parse_payload(result)
        self.__queue_command(109, '')

    def pause(self) -> None:
        _log.debug("Attempting to pause mowing: %r", self.__state)
        if self.__state in ("MOWING", "FIXED_MOWING"):
            self.__queue_command(115, "PauseWork")
            self.__wait_for_state('PAUSED')
        else:
            _log.error("Unable to pause due to current state: %r", self.__state)
            raise MoeBotStateException()

    def cancel(self) -> None:
        _log.debug("Attempting to cancel mowing: %r", self.__state)
        if self.__state in ("PAUSED", "CHARGING_WITH_TASK_SUSPEND", "PARK"):
            self.__queue_command(115, "CancelWork")
            self.__wait_for_state('STANDBY')
        else:
            _log.error("Unable to cancel due to current state: %r", self.__state)
            raise MoeBotStateException()

    def dock(self) -> None:
        _log.debug("Attempting to dock mower: %r", self.__state)
        if self.__state in ("STANDBY", "STANDBY"):
            self.__queue_command(115, "StartReturnStation")
            self.__wait_for_state('PARK')
        else:
            _log.error("Unable to dock due to current state: %r", self.__state)
            raise MoeBotStateException()

    def __repr__(self) -> str:
        return "[MoeBot - {id: %s, state: %s, battery: %s}]" % (self.id, self.__state, self.__battery)


class MoeBotStateException(Exception):
    pass


class MoeBotConnectionError(Exception):
    pass


class MoeBotConfigException(Exception):
    pass
