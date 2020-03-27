import unittest

from wasmtime import *

import faulthandler
faulthandler.enable()


class TestFunc(unittest.TestCase):
    def test_smoke(self):
        store = Store()
        ty = FuncType([], [])
        func = Func(store, ty, lambda: None)
        func.call()
        self.assertEqual(func.param_arity(), 0)
        self.assertEqual(func.result_arity(), 0)
        self.assertTrue(func.as_extern().type().func_type() is not None)
        self.assertTrue(func.as_extern().type().memory_type() is None)
        self.assertTrue(func.as_extern().type().global_type() is None)
        self.assertTrue(func.as_extern().type().table_type() is None)

    def test_add(self):
        store = Store()
        ty = FuncType([ValType.i32(), ValType.i32()], [ValType.i32()])
        func = Func(store, ty, lambda a, b: a + b)
        self.assertEqual(func.call(1, 2), 3)

    def test_calls(self):
        store = Store()
        ty = FuncType([ValType.i32()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 1))
        func.call(1)

        ty = FuncType([ValType.i64()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 2))
        func.call(Val.i64(2))

        ty = FuncType([ValType.f32()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 3.0))
        func.call(3.0)

        ty = FuncType([ValType.f64()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 4.0))
        func.call(4.0)

    def test_multi_return(self):
        store = Store()
        ty = FuncType([], [ValType.i32(), ValType.i32()])
        func = Func(store, ty, lambda: [1, 2])
        self.assertEqual(func.call(), [1, 2])

    def test_errors(self):
        store = Store()
        ty = FuncType([], [])
        with self.assertRaises(TypeError):
            Func(1, ty, lambda: None)
        with self.assertRaises(TypeError):
            Func(store, 1, lambda: None)
        func = Func(store, ty, lambda: None)
        with self.assertRaises(TypeError):
            func.call(2)

        ty = FuncType([ValType.i32()], [])
        func = Func(store, ty, lambda: None)
        with self.assertRaises(TypeError):
            func.call(3.0)
        with self.assertRaises(TypeError):
            func.call(Val.i64(3))
        ty = FuncType([ValType.i32()], [])

        func = Func(store, ty, lambda x: x)
        with self.assertRaises(RuntimeError):
            func.call(1)

    def test_produce_wrong(self):
        store = Store()
        ty = FuncType([], [ValType.i32(), ValType.i32()])
        func = Func(store, ty, lambda: 1)
        with self.assertRaises(RuntimeError):
            func.call()
        func = Func(store, ty, lambda: [1, 2, 3])
        with self.assertRaises(RuntimeError):
            func.call()

    def test_typest(self):
        store = Store()
        i32 = ValType.i32()
        i64 = ValType.i64()
        f32 = ValType.f32()
        f64 = ValType.f64()
        ty = FuncType([i32, i64, f32, f64], [f64, f32, i64, i32])

        def rev(*args):
            ret = list(args)
            ret.reverse()
            return ret

        func = Func(store, ty, rev)
        self.assertEqual(func.call(1, 2, 3.0, 4.0), [4.0, 3.0, 2, 1])
