import unittest

from wasmtime import *


class TestTable(unittest.TestCase):
    def test_new(self):
        store = Store()
        module = Module(store, """
            (module (table (export "") 1 funcref))
        """)
        table = Instance(module, []).exports[0]
        self.assertTrue(isinstance(table, Table))
        self.assertEqual(table.type.limits, Limits(1, None))
        self.assertEqual(table.size, 1)
