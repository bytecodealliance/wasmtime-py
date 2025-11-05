import unittest

from wasmtime import Store, WasmtimeError
from wasmtime.component import *


class TestValue(unittest.TestCase):
    def test_resource_type(self):
        r1 = ResourceType.host(1)
        r2 = ResourceType.host(2)
        r3 = ResourceType.host(1)
        self.assertNotEqual(r1, r2)
        self.assertEqual(r1, r3)

    def test_resource_host(self):
        store = Store()
        r1 = ResourceHost.own(42, 1)

        r2 = r1.to_any(store)
        self.assertEqual(r2.type, ResourceType.host(1))
        self.assertTrue(r2.owned)

        r3 = r2.to_host(store)
        self.assertTrue(r3.owned)
        self.assertEqual(r3.rep, 42)
        self.assertEqual(r3.type, 1)

        with self.assertRaises(WasmtimeError):
            r2.drop(store)

        r4 = r3.to_any(store)
        r4.drop(store)

        r5 = ResourceHost.borrow(84, 2)
        self.assertFalse(r5.owned)
        self.assertEqual(r5.rep, 84)
        self.assertEqual(r5.type, 2)

        with self.assertRaises(WasmtimeError):
            ResourceHost()

    def test_resource_host_dtor(self):
        store = Store()
        linker = Linker(store.engine)

        def drop(_store, rep):
            self.assertEqual(rep, 100)

        with linker.root() as l:
            l.add_resource('t', ResourceType.host(23), drop)

        component = Component(store.engine, """
            (component
                (import "t" (type $t (sub resource)))
                (core func $drop (canon resource.drop $t))
                (core module $a
                    (import "" "drop" (func $drop (param i32)))
                    (func (export "drop") (param i32)
                        local.get 0
                        call $drop)
                )
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "drop" (func $drop))
                    ))
                ))
                (func (export "drop") (param "x" (own $t))
                    (canon lift (core func $a "drop")))
            )
        """)
        instance = linker.instantiate(store, component)
        f = instance.get_func(store, 'drop')
        assert(f is not None)

        with self.assertRaises(WasmtimeError):
            f(store, ResourceHost.own(1, 2))

        instance = linker.instantiate(store, component)
        f = instance.get_func(store, 'drop')
        assert(f is not None)
        f(store, ResourceHost.own(100, 23))

    def test_exception_in_host_resource_dtor(self):
        store = Store()
        linker = Linker(store.engine)

        def drop(_store, _rep):
            raise RuntimeError('oh no')

        with linker.root() as l:
            l.add_resource('t', ResourceType.host(2), drop)

        component = Component(store.engine, """
            (component
                (import "t" (type $t (sub resource)))
                (core func $drop (canon resource.drop $t))
                (core module $a
                    (import "" "drop" (func $drop (param i32)))
                    (func (export "drop") (param i32)
                        local.get 0
                        call $drop)
                )
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "drop" (func $drop))
                    ))
                ))
                (func (export "drop") (param "x" (own $t))
                    (canon lift (core func $a "drop")))
            )
        """)
        instance = linker.instantiate(store, component)
        f = instance.get_func(store, 'drop')
        assert(f is not None)

        with self.assertRaises(RuntimeError) as cm:
            f(store, ResourceHost.own(1, 2))
        self.assertEqual(str(cm.exception), 'oh no')

    def test_resource_any(self):
        with self.assertRaises(WasmtimeError):
            ResourceAny()

        store = Store()
        linker = Linker(store.engine)

        component = Component(store.engine, """
            (component
                (type $t' (resource (rep i32)))
                (export $t "t" (type $t'))
                (core func $new (canon resource.new $t))
                (core func $drop (canon resource.drop $t))
                (core module $a
                    (import "" "new" (func $new (param i32) (result i32)))
                    (import "" "drop" (func $drop (param i32)))
                    (func (export "new") (param i32) (result i32)
                        local.get 0
                        call $new)
                    (func (export "drop") (param i32)
                        local.get 0
                        call $drop)
                )
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "new" (func $new))
                        (export "drop" (func $drop))
                    ))
                ))
                (func (export "new") (param "x" u32) (result (own $t))
                    (canon lift (core func $a "new")))
                (func (export "drop") (param "x" (own $t))
                    (canon lift (core func $a "drop")))
            )
        """)
        instance = linker.instantiate(store, component)
        new = instance.get_func(store, 'new')
        drop = instance.get_func(store, 'drop')
        assert(new is not None)
        assert(drop is not None)

        r1 = new(store, 100)
        new.post_return(store)
        r2 = new(store, 200)
        new.post_return(store)

        with self.assertRaises(WasmtimeError):
            r1.to_host(store)

        r1.drop(store)
        drop(store, r2)
        drop.post_return(store)

        with self.assertRaises(WasmtimeError):
            drop(store, ResourceHost.own(1, 1))
