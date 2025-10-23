import unittest

from wasmtime import Engine, WasmtimeError, Module, Store
from wasmtime.component import Linker, Component, LinkerInstance


class TestLinker(unittest.TestCase):
    def test_smoke(self):
        engine = Engine()
        linker = Linker(engine)
        linker.allow_shadowing = True
        linker.allow_shadowing = False

    def test_init_linker_instance(self):
        with self.assertRaises(WasmtimeError):
            LinkerInstance()

    def test_root(self):
        engine = Engine()
        linker = Linker(engine)
        with linker.root() as root:
            pass
        with linker.root() as root:
            with self.assertRaises(WasmtimeError):
                linker.root()
        with linker.root() as root:
            pass

    def test_add_instance(self):
        engine = Engine()
        linker = Linker(engine)
        with linker.root() as root:
            with root.add_instance('x'):
                pass
            with root.add_instance('y'):
                pass
            with self.assertRaises(WasmtimeError):
                root.add_instance('x')
            with self.assertRaises(WasmtimeError):
                root.add_instance('y')
            with root.add_instance('z'):
                pass

        with linker.root() as root:
            with root.add_instance('again'):
                pass

        with linker.root() as root:
            with root.add_instance('another') as x:
                # Reuse `root` while `x` is alive
                with self.assertRaises(WasmtimeError):
                    root.add_instance('y')

                # Reuse `x` while `x` is alive
                with x.add_instance('x'):
                    with self.assertRaises(WasmtimeError):
                        x.add_instance('y')

    def test_add_module(self):
        engine = Engine()
        linker = Linker(engine)
        with linker.root() as root:
            root.add_module('x', Module(engine, b'(module)'))
            root.add_module('y', Module(engine, b'(module)'))

            with self.assertRaises(WasmtimeError):
                root.add_module('x', Module(engine, b'(module)'))

            with root.add_instance('z'):
                with self.assertRaises(WasmtimeError):
                    root.add_module('not-used-yet', Module(engine, b'(module)'))

    def test_add_wasip2(self):
        engine = Engine()
        linker = Linker(engine)
        linker.add_wasip2()

        with linker.root():
            with self.assertRaises(WasmtimeError):
                linker.add_wasip2()

        linker.close()

        with Linker(engine) as l2:
            l2.add_wasip2()
            with self.assertRaises(WasmtimeError):
                l2.add_wasip2()
            l2.allow_shadowing = True
            l2.add_wasip2()

    def test_host_exception(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, """
            (component
                (import "x" (func $x))
                (core module $a
                    (import "" "x" (func))
                    (func (export "x") call 0)
                )
                (core func $x (canon lower (func $x)))
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "x" (func $x))
                    ))
                ))
                (func (export "x") (canon lift (core func $a "x")))
            )
        """)
        def host_func(_store):
            raise RuntimeError("oh no")
        linker = Linker(engine)
        with linker.root() as l:
            l.add_func('x', host_func)
        instance = linker.instantiate(store, component)
        func = instance.get_func(store, 'x')
        assert(func is not None)
        with self.assertRaises(RuntimeError) as cm:
            func(store)
        self.assertEqual(str(cm.exception), "oh no")

    def test_fail_instantiate(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, """
            (component
                (import "x" (func $x))
            )
        """)
        linker = Linker(engine)
        with self.assertRaises(WasmtimeError):
            linker.instantiate(store, component)

    def test_shadow_func(self):
        engine = Engine()
        store = Store(engine)
        linker = Linker(engine)
        with linker.root() as l:
            l.add_func('x', lambda: None)
            with self.assertRaises(WasmtimeError):
                l.add_func('x', lambda: None)
        linker.allow_shadowing = True
        with linker.root() as l:
            l.add_func('x', lambda: None)
