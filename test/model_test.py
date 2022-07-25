import unittest
from pymoebot import MoeBotConnectionError, MoeBot

class TestMoeBot(unittest.TestCase):
    def test_no_device(self):
        self.assertRaises(MoeBotConnectionError, MoeBot("RANDOM", "127.0.0.1", "RANDOM_KEY_ABCDE"))
        