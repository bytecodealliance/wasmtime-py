import unittest

from wasmtime import Engine, WasmtimeError, Store
from wasmtime.component import Linker, Component, Instance


class TestInstance(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(WasmtimeError):
            Instance()

    def test_smoke(self):
        engine = Engine()
        linker = Linker(engine)
        component = Component(engine, '(component)')
        store = Store(engine)

        instance = linker.instantiate(store, component)
        self.assertIsNotNone(instance)
        self.assertIsNone(instance.get_export_index(store, 'hello'))

        component = Component(engine, """
            (component
                (core module (export "foo"))
            )
        """)
        instance = linker.instantiate(store, component)
        self.assertIsNotNone(instance.get_export_index(store, 'foo'))

        component = Component(engine, """
            (component
                (core module $a)
                (instance (export "x")
                    (export "m" (core module $a))
                )
            )
        """)
        instance = linker.instantiate(store, component)
        e1 = instance.get_export_index(store, 'x')
        e2 = component.get_export_index('x')
        assert(e1 is not None)
        assert(e2 is not None)
        self.assertIsNotNone(instance.get_export_index(store, 'm', instance = e1))
        self.assertIsNotNone(instance.get_export_index(store, 'm', instance = e2))

        self.assertIsNone(instance.get_func(store, e1))
        self.assertIsNone(instance.get_func(store, e2))

    def test_get_func(self):
        engine = Engine()
        linker = Linker(engine)
        store = Store(engine)

        component = Component(engine, """
            (component
                (core module $a
                    (func (export "foo"))
                )
                (core instance $a (instantiate $a))
                (func (export "a") (canon lift (core func $a "foo")))
            )
        """)
        instance = linker.instantiate(store, component)
        index = instance.get_export_index(store, 'a')
        assert(index is not None)
        func = instance.get_func(store, index)
        self.assertIsNotNone(func)

        self.assertIsNotNone(instance.get_func(store, 'a'))
        self.assertIsNone(instance.get_func(store, 'b'))
