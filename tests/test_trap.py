import unittest

from wasmtime import *

class TestTrap(unittest.TestCase):
    def test_new(self):
        store = Store()
        trap = Trap(store, 'x')
        self.assertEqual(trap.message(), 'x')
