import unittest

from wasmtime import *


class TestInstance(unittest.TestCase):
    def test_smoke(self):
        store = Store()
        module = Module(store.engine, '(module)')
        Instance(store, module, [])

    def test_export_func(self):
        store = Store()
        module = Module(store.engine, '(module (func (export "")))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        assert(isinstance(extern, Func))
        assert(isinstance(extern.type, FuncType))

        extern()

        assert(instance.exports[''] is not None)
        with self.assertRaises(KeyError):
            instance.exports['x']
        with self.assertRaises(IndexError):
            instance.exports[100]
        assert(instance.exports.get('x') is None)
        assert(instance.exports.get(2) is None)

    def test_export_global(self):
        store = Store()
        module = Module(
            store.engine, '(module (global (export "") i32 (i32.const 3)))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        assert(isinstance(extern, Global))
        self.assertEqual(extern.value, 3)
        assert(isinstance(extern.type, GlobalType))

    def test_export_memory(self):
        store = Store()
        module = Module(store.engine, '(module (memory (export "") 1))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        assert(isinstance(extern, Memory))
        self.assertEqual(extern.size, 1)

    def test_export_table(self):
        store = Store()
        module = Module(store.engine, '(module (table (export "") 1 funcref))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        assert(isinstance(extern, Table))

    def test_multiple_exports(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (func (export "a"))
                (func (export "b"))
                (global (export "c") i32 (i32.const 0))
            )
        """)
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 3)
        assert(isinstance(instance.exports[0], Func))
        assert(isinstance(instance.exports[1], Func))
        assert(isinstance(instance.exports[2], Global))

    def test_import_func(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (import "" "" (func))
                (start 0)
            )
        """)
        hit = []
        func = Func(store, FuncType([], []), lambda: hit.append(True))
        Instance(store, module, [func])
        assert(len(hit) == 1)
        Instance(store, module, [func])
        assert(len(hit) == 2)

    def test_import_global(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (import "" "" (global (mut i32)))
                (func (export "") (result i32)
                    global.get 0)
                (func (export "update")
                    i32.const 5
                    global.set 0)
            )
        """)
        g = Global(store, GlobalType(ValType.i32(), True), 2)
        instance = Instance(store, module, [g])
        f = instance.exports[0]
        assert(isinstance(f, Func))

        self.assertEqual(f(), 2)
        g.value = 4
        self.assertEqual(f(), 4)

        instance2 = Instance(store, module, [g])
        f2 = instance2.exports[0]
        assert(isinstance(f2, Func))
        self.assertEqual(f(), 4)
        self.assertEqual(f2(), 4)

        update = instance.exports[1]
        assert(isinstance(update, Func))
        update()
        self.assertEqual(f(), 5)
        self.assertEqual(f2(), 5)

    def test_import_memory(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (import "" "" (memory 1))
            )
        """)
        m = Memory(store, MemoryType(Limits(1, None)))
        Instance(store, module, [m])

    def test_import_table(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (table (export "") 1 funcref)
            )
        """)
        table = Instance(store, module, []).exports[0]

        module = Module(store.engine, """
            (module
                (import "" "" (table 1 funcref))
            )
        """)
        Instance(store, module, [table])

    def test_invalid(self):
        store = Store()
        with self.assertRaises(TypeError):
            Instance(store, 1, [])  # type: ignore
        with self.assertRaises(TypeError):
            Instance(store, Module(store.engine, '(module (import "" "" (func)))'), [1])  # type: ignore

        val = Func(store, FuncType([], []), lambda: None)
        module = Module(store.engine, '(module (import "" "" (func)))')
        Instance(store, module, [val])
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [])
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [val, val])

        module = Module(store.engine, '(module (import "" "" (global i32)))')
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [val])

    def test_start_trap(self):
        store = Store()
        module = Module(store.engine, '(module (func unreachable) (start 0))')
        with self.assertRaises(Trap):
            Instance(store, module, [])
