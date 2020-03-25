import unittest

from wasmtime import *


class TestTypes(unittest.TestCase):
    def test_valtype(self):
        i32 = ValType.i32()
        i64 = ValType.i64()
        f32 = ValType.f32()
        f64 = ValType.f64()
        anyref = ValType.anyref()
        funcref = ValType.funcref()
        self.assertEqual(i32, i32)
        self.assertNotEqual(i32, f32)
        self.assertNotEqual(i32, 1.0)
        self.assertEqual(i32, ValType.i32())
        self.assertEqual(str(i32), 'i32')
        self.assertEqual(str(i64), 'i64')
        self.assertEqual(str(f32), 'f32')
        self.assertEqual(str(f64), 'f64')
        self.assertEqual(str(anyref), 'anyref')
        self.assertEqual(str(funcref), 'funcref')

    def test_func_type(self):
        ty = FuncType([], [])
        self.assertEqual([], ty.params())
        self.assertEqual([], ty.results())

        ty = FuncType([ValType.i32()], [ValType.i64()])
        self.assertEqual([ValType.i32()], ty.params())
        self.assertEqual([ValType.i64()], ty.results())

        GlobalType(ty.params()[0], True)

    def test_global_type(self):
        ty = GlobalType(ValType.i32(), True)
        self.assertTrue(ty.mutable())
        self.assertEqual(ty.content(), ValType.i32())

        ty = GlobalType(ValType.i64(), False)
        self.assertFalse(ty.mutable())
        self.assertEqual(ty.content(), ValType.i64())

    def test_table_type(self):
        ty = TableType(ValType.i32(), Limits(1, None))
        self.assertEqual(ty.element(), ValType.i32())
        self.assertEqual(ty.limits(), Limits(1, None))

        ty = TableType(ValType.f32(), Limits(1, 2))
        self.assertEqual(ty.element(), ValType.f32())
        self.assertEqual(ty.limits(), Limits(1, 2))

    def test_memory_type(self):
        ty = MemoryType(Limits(1, None))
        self.assertEqual(ty.limits(), Limits(1, None))

        ty = MemoryType(Limits(1, 2))
        self.assertEqual(ty.limits(), Limits(1, 2))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            MemoryType(1)
        with self.assertRaises(TypeError):
            TableType(1)
        with self.assertRaises(TypeError):
            TableType(ValType.i32())

        ty = ValType.i32()
        TableType(ty, Limits(1, None))
        TableType(ty, Limits(1, None))

        ty = ValType.i32()
        TableType(ty, Limits(1, None))
        GlobalType(ty, True)
        with self.assertRaises(TypeError):
            GlobalType(1, True)

        with self.assertRaises(TypeError):
            FuncType([1], [])
        with self.assertRaises(TypeError):
            FuncType([], [2])

        ty = ValType.i32()
        TableType(ty, Limits(1, None))
        FuncType([ty], [])
        FuncType([], [ty])

        with self.assertRaises(RuntimeError):
            ValType()
