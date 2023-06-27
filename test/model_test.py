import unittest
from unittest import mock

from pymoebot import MoeBotConnectionError, MoeBot


class TestMoeBot(unittest.TestCase):
    @mock.patch('tinytuya.Device.status')
    def test_no_device(self, mock_status):
        mock_status.return_value = {'Error': 'Network Error: Device Unreachable', 'Err': '905', 'Payload': None}

        m = MoeBot("RANDOM", "127.0.0.1", "RANDOM_KEY_ABCDE")
        self.assertFalse(m.online)
        self.assertIsNone(m.state)

    @mock.patch('tinytuya.Device.status')
    def test_mock_device(self, mock_status):
        mock_status.return_value = {
            'dps': {'6': 100, '101': 'STANDBY', '102': 0, '103': 'MOWER_LEAN', '104': True, '105': 3, '106': 1111,
                    '114': 'AutoMode'}}

        m = MoeBot("RANDOM", "127.0.0.1", "RANDOM_KEY_ABCDE")
        self.assertFalse(m.online)
        self.assertIsNone(m.state)
        m.poll()
        self.assertTrue(m.online)
        self.assertIsNotNone(m.state)
