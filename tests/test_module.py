import unittest
import tempfile

from wasmtime import *


class TestModule(unittest.TestCase):
    def test_smoke(self):
        Module(Engine(), '(module)')
        Module(Engine(), bytes(b'\0asm\x01\0\0\0'))
        Module(Engine(), bytearray(b'\0asm\x01\0\0\0'))

    def test_invalid(self):
        with self.assertRaises(AttributeError):
            Module.validate(1, b'')  # type: ignore
        with self.assertRaises(TypeError):
            Module.validate(Store(), 2)  # type: ignore
        with self.assertRaises(TypeError):
            Module(1, b'')  # type: ignore
        with self.assertRaises(TypeError):
            Module(Engine(), 2)  # type: ignore
        with self.assertRaises(WasmtimeError):
            Module(Engine(), b'')
        with self.assertRaises(WasmtimeError):
            Module(Engine(), b'\x00')

    def test_validate(self):
        engine = Engine()
        Module.validate(engine, b'\0asm\x01\0\0\0')
        with self.assertRaises(WasmtimeError):
            Module.validate(engine, b'')

    def test_imports(self):
        store = Store()
        module = Module(store.engine, '(module)')
        self.assertEqual(module.imports, [])

        module = Module(store.engine, """
            (module
                (import "" "" (func))
                (import "a" "bcd" (global i32))
                (import "" "" (memory 1))
                (import "" "x" (table 1 funcref))
            )
        """)
        imports = module.imports
        self.assertEqual(len(imports), 4)
        self.assertEqual(imports[0].module, "")
        self.assertEqual(imports[0].name, "")
        ty = imports[0].type
        assert(isinstance(ty, FuncType))
        self.assertEqual(ty.params, [])
        self.assertEqual(ty.results, [])

        self.assertEqual(imports[1].module, "a")
        self.assertEqual(imports[1].name, "bcd")
        ty = imports[1].type
        assert(isinstance(ty, GlobalType))
        self.assertEqual(ty.content, ValType.i32())
        self.assertFalse(ty.mutable)

        self.assertEqual(imports[2].module, "")
        self.assertEqual(imports[2].name, "")
        ty = imports[2].type
        assert(isinstance(ty, MemoryType))
        self.assertEqual(ty.limits, Limits(1, None))

        self.assertEqual(imports[3].module, "")
        self.assertEqual(imports[3].name, "x")
        ty = imports[3].type
        assert(isinstance(ty, TableType))
        self.assertEqual(ty.limits, Limits(1, None))
        self.assertEqual(ty.element, ValType.funcref())

    def test_exports(self):
        store = Store()
        module = Module(store.engine, '(module)')
        self.assertEqual(module.exports, [])

        module = Module(store.engine, """
            (module
                (func (export "a") (param i32 f32) (result f64)
                    f64.const 0)
                (global (export "") (mut i32) (i32.const 1))
                (memory (export "mem") 1)
                (table (export "table") 1 funcref)
            )
        """)
        exports = module.exports
        self.assertEqual(len(exports), 4)
        self.assertEqual(exports[0].name, "a")
        ty = exports[0].type
        assert(isinstance(ty, FuncType))
        self.assertEqual(ty.params, [ValType.i32(), ValType.f32()])
        self.assertEqual(ty.results, [ValType.f64()])

        self.assertEqual(exports[1].name, "")
        ty = exports[1].type
        assert(isinstance(ty, GlobalType))
        self.assertEqual(ty.content, ValType.i32())
        self.assertTrue(ty.mutable)

        self.assertEqual(exports[2].name, "mem")
        ty = exports[2].type
        assert(isinstance(ty, MemoryType))
        self.assertEqual(ty.limits, Limits(1, None))

        self.assertEqual(exports[3].name, "table")
        ty = exports[3].type
        assert(isinstance(ty, TableType))
        self.assertEqual(ty.limits, Limits(1, None))
        self.assertEqual(ty.element, ValType.funcref())

    def test_type(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (import "" "" (func))
                (import "a" "bcd" (global i32))
                (import "" "x" (table 1 funcref))

                (func (export "a") (param i32 f32) (result f64)
                    f64.const 0)
                (global (export "") (mut i32) (i32.const 1))
                (memory (export "mem") 1)
                (table (export "table") 1 funcref)
            )
        """)
        ty = module.type
        imports = ty.imports
        exports = ty.exports
        assert(imports[0].module == '')
        assert(imports[0].name == '')
        assert(isinstance(imports[0].type, FuncType))
        assert(imports[1].module == 'a')
        assert(imports[1].name == 'bcd')
        assert(isinstance(imports[1].type, GlobalType))
        assert(imports[2].module == '')
        assert(imports[2].name == 'x')
        assert(isinstance(imports[2].type, TableType))

        assert(exports[0].name == 'a')
        assert(isinstance(exports[0].type, FuncType))
        assert(exports[1].name == '')
        assert(isinstance(exports[1].type, GlobalType))
        assert(exports[2].name == 'mem')
        assert(isinstance(exports[2].type, MemoryType))
        assert(exports[3].name == 'table')
        assert(isinstance(exports[3].type, TableType))

    def test_serialize(self):
        engine = Engine()
        module = Module(engine, '(module)')
        encoded = module.serialize()
        module = Module.deserialize(engine, encoded)
        assert(len(module.imports) == 0)
        assert(len(module.exports) == 0)
        with tempfile.TemporaryDirectory() as d:
            path = d + '/module.bin'
            with open(path, 'wb') as f:
                f.write(encoded)
            module = Module.deserialize_file(engine, path)
            assert(len(module.imports) == 0)
            assert(len(module.exports) == 0)

            # Run the destructor for `Module` which has an mmap to the file
            # which prevents deletion on Windows.
            del module
