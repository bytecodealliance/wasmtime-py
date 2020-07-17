import unittest

from wasmtime import *


class TestGlobal(unittest.TestCase):
    def test_new(self):
        store = Store()
        ty = GlobalType(ValType.i32(), True)
        g = Global(store, ty, Val.i32(1))
        Global(store, ty, Val.i32(1))
        self.assertEqual(g.type.content, ValType.i32())
        self.assertTrue(g.type.mutable)

        self.assertEqual(g.value, 1)
        g.value = Val.i32(2)
        self.assertEqual(g.value, 2)
        self.assertTrue(isinstance(g.type, GlobalType))

    def test_errors(self):
        store = Store()
        ty = GlobalType(ValType.i32(), True)
        with self.assertRaises(TypeError):
            Global(store, ty, store)
        with self.assertRaises(TypeError):
            Global(store, 1, Val.i32(1))  # type: ignore
        with self.assertRaises(TypeError):
            Global(1, ty, Val.i32(1))  # type: ignore

        g = Global(store, ty, Val.i32(1))
        with self.assertRaises(TypeError):
            g.value = g

        ty = GlobalType(ValType.i32(), False)
        g = Global(store, ty, Val.i32(1))
        with self.assertRaises(WasmtimeError):
            g.value = 1
