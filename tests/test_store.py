import unittest

from wasmtime import *

class TestStore(unittest.TestCase):
    def test_smoke(self):
        Store()
        Store(Engine())

    def test_errors(self):
        with self.assertRaises(TypeError):
            Store(3)
