import unittest
import ctypes

from functools import partial
from wasmtime import *


class TestFunc(unittest.TestCase):
    def test_smoke(self):
        store = Store()
        ty = FuncType([], [])
        func = Func(store, ty, lambda: None)
        func(store)
        self.assertTrue(isinstance(func.type(store), FuncType))

    def test_add(self):
        store = Store()
        ty = FuncType([ValType.i32(), ValType.i32()], [ValType.i32()])
        func = Func(store, ty, lambda a, b: a + b)
        self.assertEqual(func(store, 1, 2), 3)

    def test_simd_i8x16_add(self):
        # i8x16.add is SIMD 128-bit vector of i8 items of size 16
        store = Store()
        module = Module(
            store.engine,
            """
        (module
        (func $add_v128 (param $a v128) (param $b v128) (result v128)
            local.get $a
            local.get $b
            i8x16.add
        )
        (export "add_v128" (func $add_v128))
        )
        """,
        )

        instance = Instance(store, module, [])
        vector_type = ctypes.c_uint8 * 16
        add_v128_f = instance.exports(store)["add_v128"]
        if not isinstance(add_v128_f, Func):
            raise TypeError("expecting Func")
        add_v128 = partial(add_v128_f, store)
        a = vector_type(*(i for i in range(16)))
        b = vector_type(*(40 + i for i in range(16)))
        c = add_v128(a, b)
        self.assertEqual([v for v in c], [i + j for i, j in zip(a, b)])

    def test_calls(self):
        store = Store()
        ty = FuncType([ValType.i32()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 1))
        func(store, 1)

        ty = FuncType([ValType.i64()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 2))
        func(store, Val.i64(2))

        ty = FuncType([ValType.f32()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 3.0))
        func(store, 3.0)

        ty = FuncType([ValType.f64()], [])
        func = Func(store, ty, lambda a: self.assertEqual(a, 4.0))
        func(store, 4.0)

    def test_multi_return(self):
        store = Store()
        ty = FuncType([], [ValType.i32(), ValType.i32()])
        func = Func(store, ty, lambda: [1, 2])
        self.assertEqual(func(store), [1, 2])

    def test_errors(self):
        store = Store()
        ty = FuncType([], [])
        with self.assertRaises(TypeError):
            Func(1, ty, lambda: None)  # type: ignore
        with self.assertRaises(TypeError):
            Func(store, 1, lambda: None)  # type: ignore
        func = Func(store, ty, lambda: None)
        with self.assertRaises(WasmtimeError):
            func(store, 2)

        ty = FuncType([ValType.i32()], [])
        func = Func(store, ty, lambda: None)
        with self.assertRaises(TypeError):
            func(store, 3.0)
        with self.assertRaises(TypeError):
            func(store, Val.i64(3))
        ty = FuncType([ValType.i32()], [])

        func = Func(store, ty, lambda x: x)
        with self.assertRaises(WasmtimeError, msg="produced results"):
            func(store, 1)

    def test_produce_wrong(self):
        store = Store()
        ty = FuncType([], [ValType.i32(), ValType.i32()])
        func = Func(store, ty, lambda: 1)
        with self.assertRaises(TypeError, msg="has no len"):
            func(store)
        func = Func(store, ty, lambda: [1, 2, 3])
        with self.assertRaises(WasmtimeError, msg="wrong number of results"):
            func(store)

    def test_host_exception(self):
        store = Store()
        ty = FuncType([], [])

        def do_raise():
            raise Exception("hello")

        func = Func(store, ty, do_raise)
        with self.assertRaises(Exception, msg="hello"):
            func(store)

    def test_type(self):
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
        self.assertEqual(func(store, 1, 2, 3.0, 4.0), [4.0, 3.0, 2, 1])

    def test_access_caller(self):
        # Test that we get *something*
        store = Store()

        def runtest(caller):
            self.assertEqual(caller.get(''), None)
            self.assertEqual(caller.get('x'), None)
            self.assertEqual(caller.get('y'), None)

        Func(store, FuncType([], []), runtest, access_caller=True)(store)

        hit = {}

        # Test that `Caller` works and that it's invalidated
        def runtest2(caller):
            hit['yes'] = True
            hit['caller'] = caller

            self.assertTrue(caller.get('bar') is None)
            mem = caller.get('foo')
            self.assertTrue(isinstance(mem, Memory))

            self.assertEqual(mem.data_ptr(caller)[0], ord('f'))
            self.assertEqual(mem.data_ptr(caller)[1], ord('o'))
            self.assertEqual(mem.data_ptr(caller)[2], ord('o'))
            self.assertEqual(mem.data_ptr(caller)[3], 0)

        module = Module(store.engine, """
            (module
                (import "" "" (func))
                (memory (export "foo") 1)
                (start 0)
                (data (i32.const 0) "foo")
            )
        """)
        func = Func(store, FuncType([], []), runtest2, access_caller=True)
        Instance(store, module, [func])
        self.assertTrue(hit['yes'])
        self.assertTrue(hit['caller'].get('foo') is None)  # type: ignore

        # Test that `Caller` is invalidated even on exceptions
        hit2 = {}

        def runtest3(caller):
            hit2['caller'] = caller
            self.assertTrue(caller['foo'] is not None)
            raise WasmtimeError('foo')

        func = Func(store, FuncType([], []), runtest3, access_caller=True)
        with self.assertRaises(WasmtimeError, msg='foo'):
            Instance(store, module, [func])
        self.assertTrue(hit2['caller'].get('foo') is None)
