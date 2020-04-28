import unittest

from wasmtime import *


class TestLinker(unittest.TestCase):
    def test_define(self):
        store = Store()
        linker = Linker(store)
        linker.allow_shadowing = False

        func = Func(store, FuncType([], []), lambda: None)
        linker.define("", "a", func)

        g = Global(store, GlobalType(ValType.i32(), False), Val.i32(0))
        linker.define("", "c", g)

        mem = Memory(store, MemoryType(Limits(1, None)))
        linker.define("", "e", mem)

        module = Module(store, """
            (module (table (export "") 1 funcref))
        """)
        table = Instance(module, []).exports[0]
        linker.define("", "g", table)

        with self.assertRaises(WasmtimeError):
            linker.define("", "a", func)
        linker.allow_shadowing = True
        linker.define("", "a", func)

        with self.assertRaises(TypeError):
            linker.define("", "", 2)
        with self.assertRaises(TypeError):
            linker.define(2, "", func)
        with self.assertRaises(TypeError):
            linker.define("", 2, func)

    def test_define_instance(self):
        store = Store()
        linker = Linker(store)
        with self.assertRaises(TypeError):
            linker.define_instance("x", 2)

        module = Module(store, "(module)")
        linker.define_instance("a", Instance(module, []))

        module = Module(store, "(module (func (export \"foo\")))")
        instance = Instance(module, [])
        linker.define_instance("b", instance)
        with self.assertRaises(WasmtimeError):
            linker.define_instance("b", instance)
        linker.allow_shadowing = True
        linker.define_instance("b", instance)

    def test_define_wasi(self):
        store = Store()
        linker = Linker(store)
        instance = WasiInstance(store, "wasi_unstable", WasiConfig())
        linker.define_wasi(instance)

    def test_instantiate(self):
        store = Store()
        linker = Linker(store)

        module = Module(store, "(module (func (export \"foo\")))")
        instance = Instance(module, [])
        linker.define_instance("x", instance)

        func = Func(store, FuncType([], []), lambda: None)
        linker.define("y", "z", func)

        module = Module(store, """
            (module
                (import "x" "foo" (func))
                (import "y" "z" (func))
            )
        """)
        linker.instantiate(module)

        module = Module(store, """
            (module
                (import "x" "foo" (func))
                (import "y" "z" (global i32))
            )
        """)
        with self.assertRaises(WasmtimeError):
            linker.instantiate(module)

        module = Module(store, """
            (module
                (func unreachable)
                (start 0)
            )
        """)
        with self.assertRaises(Trap):
            linker.instantiate(module)

        module = Module(store, "(module)")
        linker.instantiate(module)

    def test_errors(self):
        linker = Linker(Store())
        with self.assertRaises(TypeError):
            linker.allow_shadowing = 2
        with self.assertRaises(TypeError):
            Linker(2)
        with self.assertRaises(TypeError):
            linker.instantiate(3)
