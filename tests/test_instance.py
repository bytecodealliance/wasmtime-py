import unittest

from wasmtime import *


class TestInstance(unittest.TestCase):
    def test_smoke(self):
        module = Module(Store(), '(module)')
        Instance(module, [])

    def test_export_func(self):
        module = Module(Store(), '(module (func (export "")))')
        instance = Instance(module, [])
        self.assertEqual(len(instance.exports()), 1)
        extern = instance.exports()[0]
        self.assertTrue(extern.func() is not None)
        self.assertTrue(extern.global_() is None)
        self.assertTrue(extern.memory() is None)
        self.assertTrue(extern.table() is None)
        self.assertTrue(extern.type().func_type() is not None)
        self.assertTrue(extern.type().global_type() is None)
        self.assertTrue(extern.type().memory_type() is None)
        self.assertTrue(extern.type().table_type() is None)

        func = extern.func()
        func.call()

    def test_export_global(self):
        module = Module(
            Store(), '(module (global (export "") i32 (i32.const 3)))')
        instance = Instance(module, [])
        self.assertEqual(len(instance.exports()), 1)
        extern = instance.exports()[0]
        g = extern.global_()
        self.assertEqual(g.get(), 3)

        self.assertTrue(extern.func() is None)
        self.assertTrue(extern.global_() is not None)
        self.assertTrue(extern.memory() is None)
        self.assertTrue(extern.table() is None)
        self.assertTrue(extern.type().func_type() is None)
        self.assertTrue(extern.type().global_type() is not None)
        self.assertTrue(extern.type().memory_type() is None)
        self.assertTrue(extern.type().table_type() is None)

    def test_export_memory(self):
        module = Module(Store(), '(module (memory (export "") 1))')
        instance = Instance(module, [])
        self.assertEqual(len(instance.exports()), 1)
        extern = instance.exports()[0]
        m = extern.memory()
        self.assertEqual(m.size(), 1)

    def test_export_table(self):
        module = Module(Store(), '(module (table (export "") 1 funcref))')
        instance = Instance(module, [])
        self.assertEqual(len(instance.exports()), 1)
        extern = instance.exports()[0]
        extern.table()

    def test_multiple_exports(self):
        module = Module(Store(), """
            (module
                (func (export "a"))
                (func (export "b"))
                (global (export "c") i32 (i32.const 0))
            )
        """)
        instance = Instance(module, [])
        self.assertEqual(len(instance.exports()), 3)
        self.assertTrue(instance.exports()[0].func() is not None)
        self.assertTrue(instance.exports()[1].func() is not None)
        self.assertTrue(instance.exports()[2].global_() is not None)

    def test_import_func(self):
        module = Module(Store(), """
            (module
                (import "" "" (func))
                (start 0)
            )
        """)
        hit = []
        func = Func(module.store, FuncType([], []), lambda: hit.append(True))
        Instance(module, [func])
        self.assertTrue(len(hit) == 1)
        Instance(module, [func.as_extern()])
        self.assertTrue(len(hit) == 2)

    def test_import_global(self):
        module = Module(Store(), """
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
        instance = Instance(module, [g])
        self.assertEqual(instance.exports()[0].func().call(), 2)
        g.set(4)
        self.assertEqual(instance.exports()[0].func().call(), 4)

        instance2 = Instance(module, [g.as_extern()])
        self.assertEqual(instance.exports()[0].func().call(), 4)
        self.assertEqual(instance2.exports()[0].func().call(), 4)

        instance.exports()[1].func().call()
        self.assertEqual(instance.exports()[0].func().call(), 5)
        self.assertEqual(instance2.exports()[0].func().call(), 5)

    def test_import_memory(self):
        module = Module(Store(), """
            (module
                (import "" "" (memory 1))
            )
        """)
        m = Memory(module.store, MemoryType(Limits(1, None)))
        Instance(module, [m])
        Instance(module, [m.as_extern()])

    def test_import_table(self):
        store = Store()
        module = Module(store, """
            (module
                (table (export "") 1 funcref)
            )
        """)
        table = Instance(module, []).exports()[0].table()

        module = Module(store, """
            (module
                (import "" "" (table 1 funcref))
            )
        """)
        Instance(module, [table])
        Instance(module, [table.as_extern()])

    def test_invalid(self):
        store = Store()
        with self.assertRaises(TypeError):
            Instance(1, [])
        with self.assertRaises(TypeError):
            Instance(Module(store, '(module (import "" "" (func)))'), [1])

        val = Func(store, FuncType([], []), lambda: None)
        module = Module(store, '(module (import "" "" (func)))')
        Instance(module, [val])
        with self.assertRaises(RuntimeError):
            Instance(module, [])
        with self.assertRaises(RuntimeError):
            Instance(module, [val, val])

        module = Module(store, '(module (import "" "" (global i32)))')
        with self.assertRaises(RuntimeError):
            Instance(module, [val])

    def test_start_trap(self):
        store = Store()
        module = Module(store, '(module (func unreachable) (start 0))')
        with self.assertRaises(RuntimeError):
            Instance(module, [])
