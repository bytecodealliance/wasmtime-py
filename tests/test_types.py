import unittest

from wasmtime import *

class TestTypes(unittest.TestCase):
    def test_valtype(self):
        i32 = ValType.i32()
        i64 = ValType.i64()
        f32 = ValType.f32()
        f64 = ValType.f64()
        self.assertEqual(i32, i32)
        self.assertNotEqual(i32, f32)
        self.assertEqual(i32, ValType.i32())
        self.assertEqual(str(ValType.i32()), 'i32')

    def test_func_type(self):
        ty = FuncType([], [])
        self.assertEqual([], ty.params())
        self.assertEqual([], ty.results())
        ty = FuncType([ValType.i32()], [ValType.i64()])
        self.assertEqual([ValType.i32()], ty.params())
        self.assertEqual([ValType.i64()], ty.results())

    def test_global_type(self):
        ty = GlobalType(ValType.i32(), True)
        self.assertTrue(ty.mutable())
        self.assertEqual(ty.content(), ValType.i32())

        ty = GlobalType(ValType.i64(), False)
        self.assertFalse(ty.mutable())
        self.assertEqual(ty.content(), ValType.i64())
