import unittest

from wasmtime import *

class TestModule(unittest.TestCase):
    def test_smoke(self):
        Module(Store(), '(module)')

    def test_invalid(self):
        with self.assertRaises(TypeError):
            Module(1, b'')
        with self.assertRaises(TypeError):
            Module(Store(), 2)
        with self.assertRaises(RuntimeError):
            Module(Store(), b'')
        with self.assertRaises(RuntimeError):
            Module(Store(), b'\x00')
