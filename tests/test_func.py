import unittest

from wasmtime import *


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

    def test_access_caller(self):
        # Test that we get *something*
        store = Store()
        def runtest(caller):
            self.assertEqual(caller.get_export(''), None)
            self.assertEqual(caller.get_export('x'), None)
            self.assertEqual(caller.get_export('y'), None)

        Func(store, FuncType([], []), runtest, access_caller=True).call()

        hit = {}

        # Test that `Caller` works and that it's invalidated
        def runtest2(caller):
            hit['yes'] = True
            hit['caller'] = caller

            self.assertTrue(caller.get_export('bar') is None)
            mem = caller.get_export('foo').memory()
            self.assertTrue(mem is not None)

            self.assertEqual(mem.data_ptr()[0], ord('f'))
            self.assertEqual(mem.data_ptr()[1], ord('o'))
            self.assertEqual(mem.data_ptr()[2], ord('o'))
            self.assertEqual(mem.data_ptr()[3], 0)

        module = Module(store, """
            (module
                (import "" "" (func))
                (memory (export "foo") 1)
                (start 0)
                (data (i32.const 0) "foo")
            )
        """)
        func = Func(store, FuncType([], []), runtest2, access_caller=True)
        Instance(module, [func])
        self.assertTrue(hit['yes'])
        self.assertTrue(hit['caller'].get_export('foo') is None)

        # Test that `Caller` is invalidated even on exceptions
        hit2 = {}

        def runtest3(caller):
            hit2['caller'] = caller
            self.assertTrue(caller.get_export('foo') is not None)
            raise RuntimeError('foo')

        func = Func(store, FuncType([], []), runtest3, access_caller=True)
        with self.assertRaises(RuntimeError):
            Instance(module, [func])
        self.assertTrue(hit2['caller'].get_export('foo') is None)
