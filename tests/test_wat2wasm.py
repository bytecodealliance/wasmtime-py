import unittest

from wasmtime import *


class TestWat2Wasm(unittest.TestCase):
    def test_wat2wasm(self):
        engine = Engine()
        wasm = wat2wasm(engine, '(module)')
        self.assertEqual(wasm, b'\0asm\x01\0\0\0')

    def test_errors(self):
        engine = Engine()
        with self.assertRaises(RuntimeError):
            wat2wasm(engine, 'x')
        with self.assertRaises(TypeError):
            wat2wasm(None, '(module)')
        with self.assertRaises(TypeError):
            wat2wasm(2, '(module)')
