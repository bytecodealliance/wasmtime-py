import unittest

from wasmtime import *


class TestWat2Wasm(unittest.TestCase):
    def test_wat2wasm(self):
        wasm = wat2wasm('(module)')
        self.assertEqual(wasm, b'\0asm\x01\0\0\0')

    def test_errors(self):
        with self.assertRaises(RuntimeError):
            wat2wasm('x')
