import unittest

from wasmtime import *


class TestModule(unittest.TestCase):
    def test_smoke(self):
        Module(Store(), '(module)')

    def test_invalid(self):
        with self.assertRaises(TypeError):
            Module.validate(1, b'')
        with self.assertRaises(TypeError):
            Module.validate(Store(), 2)
        with self.assertRaises(TypeError):
            Module(1, b'')
        with self.assertRaises(TypeError):
            Module(Store(), 2)
        with self.assertRaises(RuntimeError):
            Module(Store(), b'')
        with self.assertRaises(RuntimeError):
            Module(Store(), b'\x00')

    def test_validate(self):
        store = Store()
        self.assertTrue(Module.validate(store, b'\0asm\x01\0\0\0'))
        self.assertFalse(Module.validate(store, b''))

    def test_imports(self):
        store = Store()
        module = Module(store, '(module)')
        self.assertEqual(module.imports(), [])

        module = Module(store, """
            (module
                (import "" "" (func))
                (import "a" "bcd" (global i32))
                (import "" "" (memory 1))
                (import "" "x" (table 1 funcref))
            )
        """)
        imports = module.imports()
        self.assertEqual(len(imports), 4)
        self.assertEqual(imports[0].module(), "")
        self.assertEqual(imports[0].name(), "")
        ty = imports[0].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.global_type(), None)
        ty = ty.func_type()
        self.assertEqual(ty.params(), [])
        self.assertEqual(ty.results(), [])

        self.assertEqual(imports[1].module(), "a")
        self.assertEqual(imports[1].name(), "bcd")
        ty = imports[1].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.global_type()
        self.assertEqual(ty.content(), ValType.i32())
        self.assertFalse(ty.mutable())

        self.assertEqual(imports[2].module(), "")
        self.assertEqual(imports[2].name(), "")
        ty = imports[2].type()
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.global_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.memory_type()
        self.assertEqual(ty.limits(), Limits(1, None))

        self.assertEqual(imports[3].module(), "")
        self.assertEqual(imports[3].name(), "x")
        ty = imports[3].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.global_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.table_type()
        self.assertEqual(ty.limits(), Limits(1, None))
        self.assertEqual(ty.element(), ValType.funcref())

    def test_exports(self):
        store = Store()
        module = Module(store, '(module)')
        self.assertEqual(module.exports(), [])

        module = Module(store, """
            (module
                (func (export "a") (param i32 f32) (result f64)
                    f64.const 0)
                (global (export "") (mut i32) (i32.const 1))
                (memory (export "mem") 1)
                (table (export "table") 1 funcref)
            )
        """)
        exports = module.exports()
        self.assertEqual(len(exports), 4)
        self.assertEqual(exports[0].name(), "a")
        ty = exports[0].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.global_type(), None)
        ty = ty.func_type()
        self.assertEqual(ty.params(), [ValType.i32(), ValType.f32()])
        self.assertEqual(ty.results(), [ValType.f64()])

        self.assertEqual(exports[1].name(), "")
        ty = exports[1].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.global_type()
        self.assertEqual(ty.content(), ValType.i32())
        self.assertTrue(ty.mutable())

        self.assertEqual(exports[2].name(), "mem")
        ty = exports[2].type()
        self.assertEqual(ty.table_type(), None)
        self.assertEqual(ty.global_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.memory_type()
        self.assertEqual(ty.limits(), Limits(1, None))

        self.assertEqual(exports[3].name(), "table")
        ty = exports[3].type()
        self.assertEqual(ty.memory_type(), None)
        self.assertEqual(ty.global_type(), None)
        self.assertEqual(ty.func_type(), None)
        ty = ty.table_type()
        self.assertEqual(ty.limits(), Limits(1, None))
        self.assertEqual(ty.element(), ValType.funcref())
