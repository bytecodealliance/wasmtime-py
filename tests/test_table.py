# import unittest
#
# from wasmtime import *
#
# class TestTable(unittest.TestCase):
#     def test_new(self):
#         store = Store()
#         ty = TableType(ValType.funcref(), Limits(1, None))
#         table = Table(store, ty, None)
#
#         # self.assertEqual(table.type().limits(), Limits(1, None))
