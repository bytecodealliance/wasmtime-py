import unittest

from wasmtime import *

class TestConfig(unittest.TestCase):
    def test_smoke(self):
        Config()
