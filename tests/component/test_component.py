import unittest
import tempfile

from wasmtime import *
from wasmtime.component import Component, ExportIndex

class TestComponent(unittest.TestCase):
    def test_smoke(self):
        Component(Engine(), '(component)')
        Component(Engine(), bytes(b'\0asm\x0d\0\x01\0'))
        Component(Engine(), bytearray(b'\0asm\x0d\0\x01\0'))

        with self.assertRaises(WasmtimeError):
            Component(Engine(), '(component2)')
        with self.assertRaises(WasmtimeError):
            Component(Engine(), bytes(b'\0asm\x01\0\0\0'))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            Component(1, b'')  # type: ignore
        with self.assertRaises(TypeError):
            Component(Engine(), 2)  # type: ignore
        with self.assertRaises(WasmtimeError):
            Component(Engine(), b'')
        with self.assertRaises(WasmtimeError):
            Component(Engine(), b'\x00')

    def test_serialize(self):
        engine = Engine()
        component = Component(engine, '(component)')
        encoded = component.serialize()
        component = Component.deserialize(engine, encoded)
        with tempfile.TemporaryDirectory() as d:
            path = d + '/component.bin'
            with open(path, 'wb') as f:
                f.write(encoded)
            # Run the destructor for `Component` which has an mmap to the file
            # which prevents deletion on Windows.
            with Component.deserialize_file(engine, path):
                pass

    def test_exports(self):
        engine = Engine()

        c = Component(engine, '(component)')
        self.assertIsNone(c.get_export_index('foo'))
        self.assertIsNone(c.get_export_index('foo', instance = None))

        c = Component(engine, """
            (component
                (core module (export "foo"))
            )
        """)
        foo = c.get_export_index('foo')
        self.assertIsNotNone(foo)
        self.assertIsNone(c.get_export_index('foo', instance = foo))
        self.assertIsInstance(foo, ExportIndex)

        c = Component(engine, """
            (component
                (core module $a)
                (instance (export "x")
                    (export "m" (core module $a))
                )
            )
        """)
        self.assertIsNotNone(c.get_export_index('x'))
        self.assertIsNotNone(c.get_export_index('m', instance = c.get_export_index('x')))

        c2 = Component(engine, """
            (component
                (core module $a)
                (instance (export "x")
                    (export "m" (core module $a))
                )
            )
        """)
        self.assertIsNone(c2.get_export_index('m', instance = c.get_export_index('x')))
