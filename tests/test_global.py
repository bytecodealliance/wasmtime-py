import unittest

from wasmtime import *

class TestGlobal(unittest.TestCase):
    def test_new(self):
        store = Store()
        ty = GlobalType(ValType.i32(), True)
        g = Global(store, ty, Val.i32(1))
        Global(store, ty, Val.i32(1))
        self.assertEqual(g.type().content(), ValType.i32())
        self.assertTrue(g.type().mutable())

        self.assertEqual(g.get().get_i32(), 1)
        g.set(Val.i32(2));
        self.assertEqual(g.get().get_i32(), 2)

    def test_errors(self):
        store = Store()
        ty = GlobalType(ValType.i32(), True)
        with self.assertRaises(TypeError):
            Global(store, ty, 1)
        with self.assertRaises(TypeError):
            Global(store, 1, Val.i32(1))
        with self.assertRaises(TypeError):
            Global(1, ty, Val.i32(1))

        g = Global(store, ty, Val.i32(1))
        with self.assertRaises(TypeError):
            g.set(1)
