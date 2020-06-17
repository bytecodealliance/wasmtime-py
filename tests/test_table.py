import unittest

from wasmtime import *


class TestTable(unittest.TestCase):
    def test_new(self):
        store = Store()
        module = Module(store, """
            (module (table (export "") 1 funcref))
        """)
        table = Instance(store, module, []).exports[0]
        self.assertTrue(isinstance(table, Table))
        assert(isinstance(table.type, TableType))
        self.assertEqual(table.type.limits, Limits(1, None))
        self.assertEqual(table.size, 1)

        ty = TableType(ValType.i32(), Limits(1, 2))
        store = Store()
        with self.assertRaises(WasmtimeError):
            Table(store, ty, None)

        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        func = Func(store, FuncType([], []), lambda: {})
        Table(store, ty, func)

    def test_grow(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        self.assertEqual(table.size, 1)

        # type errors
        with self.assertRaises(TypeError):
            table.grow('x', None)  # type: ignore
        with self.assertRaises(TypeError):
            table.grow(2, 'x')  # type: ignore

        # growth works
        table.grow(1, None)
        self.assertEqual(table.size, 2)

        # can't grow beyond max
        with self.assertRaises(WasmtimeError):
            table.grow(1, None)

    def test_get(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        self.assertEqual(table[0], None)
        with self.assertRaises(WasmtimeError):
            self.assertEqual(table[1], None)

        called = {}
        called['hit'] = False

        def set_called():
            called['hit'] = True
        func = Func(store, FuncType([], []), set_called)
        table.grow(1, func)
        assert(not called['hit'])
        assert(isinstance(table[1], Func))
        table[1]()
        assert(called['hit'])

    def test_set(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        func = Func(store, FuncType([], []), lambda: {})
        table[0] = func
        with self.assertRaises(WasmtimeError):
            table[1] = func

    def test_errors(self):
        ty = TableType(ValType.i32(), Limits(1, 2))
        with self.assertRaises(TypeError):
            Table(1, ty, 2)  # type: ignore
        store = Store()
        with self.assertRaises(TypeError):
            Table(store, 2, 2)  # type: ignore
