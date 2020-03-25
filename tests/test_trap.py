import unittest

from wasmtime import *


class TestTrap(unittest.TestCase):
    def test_new(self):
        store = Store()
        trap = Trap(store, 'x')
        self.assertEqual(trap.message(), 'x')

    def test_errors(self):
        store = Store()
        with self.assertRaises(TypeError):
            Trap(1, '')
        with self.assertRaises(TypeError):
            Trap(store, 1)
