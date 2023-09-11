import unittest

from wasmtime import *


class TestLinker(unittest.TestCase):
    def test_define(self):
        store = Store()
        linker = Linker(store.engine)
        linker.allow_shadowing = False

        func = Func(store, FuncType([], []), lambda: None)
        linker.define(store, "", "a", func)

        g = Global(store, GlobalType(ValType.i32(), False), Val.i32(0))
        linker.define(store, "", "c", g)

        mem = Memory(store, MemoryType(Limits(1, None)))
        linker.define(store, "", "e", mem)

        module = Module(store.engine, """
            (module (table (export "") 1 funcref))
        """)
        table = Instance(store, module, []).exports(store).by_index[0]
        linker.define(store, "", "g", table)

        with self.assertRaises(WasmtimeError):
            linker.define(store, "", "a", func)
        linker.allow_shadowing = True
        linker.define(store, "", "a", func)

        with self.assertRaises(TypeError):
            linker.define(store, "", "", 2)  # type: ignore
        with self.assertRaises(AttributeError):
            linker.define(store, 2, "", func)  # type: ignore
        with self.assertRaises(AttributeError):
            linker.define(store, "", 2, func)  # type: ignore

    def test_define_instance(self):
        store = Store()
        linker = Linker(store.engine)
        with self.assertRaises(TypeError):
            linker.define_instance("x", 2)  # type: ignore

        module = Module(store.engine, "(module)")
        linker.define_instance(store, "a", Instance(store, module, []))

        module = Module(store.engine, "(module (func (export \"foo\")))")
        instance = Instance(store, module, [])
        linker.define_instance(store, "b", instance)
        with self.assertRaises(WasmtimeError):
            linker.define_instance(store, "b", instance)
        linker.allow_shadowing = True
        linker.define_instance(store, "b", instance)

    def test_define_wasi(self):
        linker = Linker(Engine())
        linker.define_wasi()

    def test_instantiate(self):
        store = Store()
        linker = Linker(store.engine)

        module = Module(store.engine, "(module (func (export \"foo\")))")
        instance = Instance(store, module, [])
        linker.define_instance(store, "x", instance)

        func = Func(store, FuncType([], []), lambda: None)
        linker.define(store, "y", "z", func)

        module = Module(store.engine, """
            (module
                (import "x" "foo" (func))
                (import "y" "z" (func))
            )
        """)
        linker.instantiate(store, module)

        module = Module(store.engine, """
            (module
                (import "x" "foo" (func))
                (import "y" "z" (global i32))
            )
        """)
        with self.assertRaises(WasmtimeError):
            linker.instantiate(store, module)

        module = Module(store.engine, """
            (module
                (func unreachable)
                (start 0)
            )
        """)
        with self.assertRaises(Trap):
            linker.instantiate(store, module)

        module = Module(store.engine, "(module)")
        linker.instantiate(store, module)

    def test_errors(self):
        linker = Linker(Engine())
        with self.assertRaises(TypeError):
            linker.allow_shadowing = 2
        with self.assertRaises(AttributeError):
            Linker(2)  # type: ignore
        with self.assertRaises(AttributeError):
            linker.instantiate(Store(), 3)  # type: ignore

    def test_module(self):
        store = Store()
        linker = Linker(store.engine)
        module = Module(store.engine, """
            (module
                (func (export "f"))
            )
        """)
        linker.define_module(store, "foo", module)
        module = Module(store.engine, """
            (module
                (import "foo" "f" (func))
            )
        """)
        linker.instantiate(store, module)

    def test_get_default(self):
        store = Store()
        linker = Linker(store.engine)
        linker.get_default(store, "foo")(store)

    def test_get_one_by_name(self):
        store = Store()
        linker = Linker(store.engine)
        with self.assertRaises(WasmtimeError):
            linker.get(store, "foo", "bar")
        module = Module(store.engine, """
            (module
                (func (export "f"))
            )
        """)
        linker.define_module(store, "foo", module)
        assert(isinstance(linker.get(store, "foo", "f"), Func))

    def test_define_func(self):
        engine = Engine()
        linker = Linker(engine)
        called = {}
        called['hits'] = 0

        def call():
            called['hits'] += 1

        linker.define_func('a', 'b', FuncType([], []), call)
        module = Module(engine, """
            (module
                (import "a" "b" (func))
                (start 0)
            )
        """)
        assert(called['hits'] == 0)
        linker.instantiate(Store(engine), module)
        assert(called['hits'] == 1)
        linker.instantiate(Store(engine), module)
        assert(called['hits'] == 2)
