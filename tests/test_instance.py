import unittest

from wasmtime import *


class TestInstance(unittest.TestCase):
    def test_smoke(self):
        store = Store()
        module = Module(store, '(module)')
        Instance(store, module, [])

    def test_export_func(self):
        store = Store()
        module = Module(store, '(module (func (export "")))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        self.assertTrue(isinstance(extern, Func))
        self.assertTrue(isinstance(extern.type, FuncType))

        extern()

        self.assertTrue(instance.exports[''] is not None)
        with self.assertRaises(KeyError):
            instance.exports['x']
        with self.assertRaises(IndexError):
            instance.exports[100]
        self.assertTrue(instance.exports.get('x') is None)
        self.assertTrue(instance.exports.get(2) is None)

    def test_export_global(self):
        store = Store()
        module = Module(
            store, '(module (global (export "") i32 (i32.const 3)))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        self.assertTrue(isinstance(extern, Global))
        self.assertEqual(extern.value, 3)
        self.assertTrue(isinstance(extern.type, GlobalType))

    def test_export_memory(self):
        store = Store()
        module = Module(store, '(module (memory (export "") 1))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        self.assertTrue(isinstance(extern, Memory))
        self.assertEqual(extern.size, 1)

    def test_export_table(self):
        store = Store()
        module = Module(store, '(module (table (export "") 1 funcref))')
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 1)
        extern = instance.exports[0]
        self.assertTrue(isinstance(extern, Table))

    def test_multiple_exports(self):
        store = Store()
        module = Module(store, """
            (module
                (func (export "a"))
                (func (export "b"))
                (global (export "c") i32 (i32.const 0))
            )
        """)
        instance = Instance(store, module, [])
        self.assertEqual(len(instance.exports), 3)
        self.assertTrue(isinstance(instance.exports[0], Func))
        self.assertTrue(isinstance(instance.exports[1], Func))
        self.assertTrue(isinstance(instance.exports[2], Global))

    def test_import_func(self):
        store = Store()
        module = Module(store, """
            (module
                (import "" "" (func))
                (start 0)
            )
        """)
        hit = []
        func = Func(module.store, FuncType([], []), lambda: hit.append(True))
        Instance(store, module, [func])
        self.assertTrue(len(hit) == 1)
        Instance(store, module, [func])
        self.assertTrue(len(hit) == 2)

    def test_import_global(self):
        store = Store()
        module = Module(store, """
            (module
                (import "" "" (global (mut i32)))
                (func (export "") (result i32)
                    global.get 0)
                (func (export "update")
                    i32.const 5
                    global.set 0)
            )
        """)
        g = Global(module.store, GlobalType(ValType.i32(), True), 2)
        instance = Instance(store, module, [g])
        self.assertEqual(instance.exports[0](), 2)
        g.value = 4
        self.assertEqual(instance.exports[0](), 4)

        instance2 = Instance(store, module, [g])
        self.assertEqual(instance.exports[0](), 4)
        self.assertEqual(instance2.exports[0](), 4)

        instance.exports[1]()
        self.assertEqual(instance.exports[0](), 5)
        self.assertEqual(instance2.exports[0](), 5)

    def test_import_memory(self):
        store = Store()
        module = Module(store, """
            (module
                (import "" "" (memory 1))
            )
        """)
        m = Memory(module.store, MemoryType(Limits(1, None)))
        Instance(store, module, [m])

    def test_import_table(self):
        store = Store()
        module = Module(store, """
            (module
                (table (export "") 1 funcref)
            )
        """)
        table = Instance(store, module, []).exports[0]

        module = Module(store, """
            (module
                (import "" "" (table 1 funcref))
            )
        """)
        Instance(store, module, [table])

    def test_invalid(self):
        store = Store()
        with self.assertRaises(TypeError):
            Instance(store, 1, [])
        with self.assertRaises(TypeError):
            Instance(store, Module(store, '(module (import "" "" (func)))'), [1])

        val = Func(store, FuncType([], []), lambda: None)
        module = Module(store, '(module (import "" "" (func)))')
        Instance(store, module, [val])
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [])
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [val, val])

        module = Module(store, '(module (import "" "" (global i32)))')
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [val])

    def test_start_trap(self):
        store = Store()
        module = Module(store, '(module (func unreachable) (start 0))')
        with self.assertRaises(Trap):
            Instance(store, module, [])
