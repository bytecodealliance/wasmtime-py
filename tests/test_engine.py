import unittest

from wasmtime import *


class TestEngine(unittest.TestCase):
    def test_smoke(self):
        Engine()
        Engine(Config())

    def test_errors(self):
        with self.assertRaises(TypeError):
            Engine(3)  # type: ignore
        config = Config()
        Engine(config)
        with self.assertRaises(WasmtimeError):
            Engine(config)
