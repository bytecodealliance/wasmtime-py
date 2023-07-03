import unittest

from wasmtime import *


class TestTable(unittest.TestCase):
    def test_new(self):
        store = Store()
        module = Module(store.engine, """
            (module (table (export "") 1 funcref))
        """)
        table = Instance(store, module, []).exports(store)[0]
        assert(isinstance(table, Table))
        assert(isinstance(table.type(store), TableType))
        self.assertEqual(table.type(store).limits, Limits(1, None))
        self.assertEqual(table.size(store), 1)

        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        func = Func(store, FuncType([], []), lambda: {})
        Table(store, ty, func)

    def test_grow(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        self.assertEqual(table.size(store), 1)

        # type errors
        with self.assertRaises(TypeError):
            table.grow(store, 'x', None)  # type: ignore
        with self.assertRaises(TypeError):
            table.grow(store, 2, 'x')

        # growth works
        table.grow(store, 1, None)
        self.assertEqual(table.size(store), 2)

        # can't grow beyond max
        with self.assertRaises(WasmtimeError):
            table.grow(store, 1, None)

    def test_get(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        self.assertEqual(table.get(store, 0), None)
        self.assertEqual(table.get(store, 1), None)

        called = {}
        called['hit'] = False

        def set_called():
            called['hit'] = True
        func = Func(store, FuncType([], []), set_called)
        table.grow(store, 1, func)
        assert(not called['hit'])
        f = table.get(store, 1)
        assert(isinstance(f, Func))
        f(store)
        assert(called['hit'])

    def test_set(self):
        ty = TableType(ValType.funcref(), Limits(1, 2))
        store = Store()
        table = Table(store, ty, None)
        func = Func(store, FuncType([], []), lambda: {})
        table.set(store, 0, func)
        with self.assertRaises(WasmtimeError):
            table.set(store, 1, func)
