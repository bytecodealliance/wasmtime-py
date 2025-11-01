import unittest
from dataclasses import dataclass
from wasmtime import Store, WasmtimeError, Engine
from wasmtime.component import *
from typing import Any, List

def list_component(ty_wit: str):
    return f"""
        (component
            (import "x" (func $x (param "x" {ty_wit}) (result {ty_wit})))
            (core module $libc
                (memory (export "mem") 1)
                (global $base (mut i32) (i32.const 100))
                (func (export "realloc") (param i32 i32 i32 i32) (result i32)
                    (local $ret i32)
                    local.get 0
                    if unreachable end
                    local.get 1
                    if unreachable end

                    (local.set $ret (global.get $base))
                    (global.set $base
                        (i32.add
                            (global.get $base)
                            (local.get 2)))
                    local.get $ret)
            )
            (core instance $libc (instantiate $libc))
            (core module $a
                (import "" "x" (func (param i32 i32 i32)))
                (func (export "x") (param i32 i32)  (result i32)
                    local.get 0
                    local.get 1
                    i32.const 0
                    call 0
                    i32.const 0)
            )
            (core func $x (canon lower (func $x)
                (memory $libc "mem") (realloc (func $libc "realloc"))))
            (core instance $a (instantiate $a
                (with "" (instance
                    (export "x" (func $x))
                ))
            ))
            (func (export "x") (param "x" {ty_wit}) (result {ty_wit})
                (canon lift (core func $a "x") (memory $libc "mem")
                (realloc (func $libc "realloc"))))
        )
    """

def retptr_component(ty_wit: str, ty_wasm: str):
    return f"""
        (component
            (type $t' {ty_wit})
            (import "t" (type $t (eq $t')))
            (import "x" (func $x (param "x" $t) (result $t)))
            (core module $libc (memory (export "mem") 1))
            (core instance $libc (instantiate $libc))
            (core module $a
                (import "" "x" (func (param {ty_wasm} i32)))
                (func (export "x") (param {ty_wasm})  (result i32)
                    local.get 0
                    local.get 1
                    i32.const 0
                    call 0
                    i32.const 0)
            )
            (core func $x (canon lower (func $x) (memory $libc "mem")))
            (core instance $a (instantiate $a
                (with "" (instance
                    (export "x" (func $x))
                ))
            ))
            (func (export "x") (param "x" $t) (result $t)
                (canon lift (core func $a "x") (memory $libc "mem")))
        )
    """

class TestFunc(unittest.TestCase):
    def roundtrip(self, wat: str, values: List[Any], bad = TypeError) -> None:
        engine = Engine()
        store = Store(engine)
        component = Component(engine, wat)
        value_being_tested = None

        def roundtrip(_store, val):
            self.assertEqual(value_being_tested, val)
            return val

        linker = Linker(engine)
        with linker.root() as l:
            l.add_func('x', roundtrip)
        instance = linker.instantiate(store, component)
        f = instance.get_func(store, 'x')
        assert(f is not None)
        for val in values:
            value_being_tested = val
            ret = f(store, val)
            self.assertEqual(ret, val)
            f.post_return(store)

        class Bad:
            pass
        with self.assertRaises(bad):
            f(store, Bad())

    def roundtrip_simple(self, ty_wit: str, ty_wasm: str, values: List[Any]) -> None:
        wat = f"""
            (component
                (type $t' {ty_wit})
                (import "t" (type $t (eq $t')))
                (import "x" (func $x (param "x" $t) (result $t)))
                (core module $a
                    (import "" "x" (func (param {ty_wasm}) (result {ty_wasm})))
                    (func (export "x") (param {ty_wasm}) (result {ty_wasm})
                        local.get 0
                        call 0)
                )
                (core func $x (canon lower (func $x)))
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "x" (func $x))
                    ))
                ))
                (func (export "x") (param "x" $t) (result $t)
                    (canon lift (core func $a "x")))
            )
        """
        self.roundtrip(wat, values)

    def test_init(self):
        with self.assertRaises(WasmtimeError):
            Func()

    def test_type_reflection(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, """
            (component
                (core module $a
                    (func (export "a"))
                    (func (export "b") (param i32) (result i32) unreachable)
                )
                (core instance $a (instantiate $a))
                (func (export "a") (canon lift (core func $a "a")))
                (func (export "b") (param "x" u32) (result u32)
                    (canon lift (core func $a "b")))
            )
        """)
        instance = Linker(engine).instantiate(store, component)
        ai = instance.get_export_index(store, 'a')
        bi = instance.get_export_index(store, 'b')
        assert(ai is not None)
        assert(bi is not None)
        a = instance.get_func(store, ai)
        b = instance.get_func(store, bi)
        assert(a is not None)
        assert(b is not None)
        self.assertEqual(a.type(store).params, [])
        self.assertIsNone(a.type(store).result)
        self.assertEqual(b.type(store).params, [('x', U32())])
        self.assertEqual(b.type(store).result, U32())

    def test_call(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, """
            (component
                (core module $a
                    (func (export "a"))
                    (func (export "b") (param i32)
                        local.get 0
                        i32.const 100
                        i32.ne
                        if unreachable end)
                    (func (export "c") (result i32) (i32.const 101))
                )
                (core instance $a (instantiate $a))
                (func (export "a") (canon lift (core func $a "a")))
                (func (export "b") (param "x" u32) (canon lift (core func $a "b")))
                (func (export "c") (result u32) (canon lift (core func $a "c")))
            )
        """)
        instance = Linker(engine).instantiate(store, component)
        a = instance.get_func(store, 'a')
        assert(a is not None)
        ret = a(store)
        self.assertEqual(ret, None)
        a.post_return(store)

        b = instance.get_func(store, 'b')
        assert(b is not None)
        ret = b(store, 100)
        self.assertEqual(ret, None)
        b.post_return(store)

        c = instance.get_func(store, 'c')
        assert(c is not None)
        ret = c(store)
        self.assertEqual(ret, 101)
        c.post_return(store)

        with self.assertRaises(TypeError):
            b(store)

    def test_roundtrip_empty(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, f"""
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

        linker = Linker(engine)
        with linker.root() as l:
            l.add_func('x', lambda _store: None)
        instance = linker.instantiate(store, component)
        f = instance.get_func(store, 'x')
        assert(f is not None)

        self.assertIsNone(f(store))
        f.post_return(store)

    def test_roundtrip_primitive(self):
        self.roundtrip_simple('bool', 'i32', [True, False])
        self.roundtrip_simple('u8', 'i32', [0, 1, 42, 255])
        self.roundtrip_simple('u16', 'i32', [0, 1, 42, 65535])
        self.roundtrip_simple('u32', 'i32', [0, 1, 42, 4294967295])
        self.roundtrip_simple('u64', 'i64', [0, 1, 42, 18446744073709551615])
        self.roundtrip_simple('s8', 'i32', [0, 1, -1, 42, -42, 127, -128])
        self.roundtrip_simple('s16', 'i32', [0, 1, -1, 42, -42, 32767, -32768])
        self.roundtrip_simple('s32', 'i32', [0, 1, -1, 42, -42, 2147483647, -2147483648])
        self.roundtrip_simple('s64', 'i64', [0, 1, -1, 42, -42, 9223372036854775807, -9223372036854775808])
        self.roundtrip_simple('f32', 'f32', [0.0, 1.0, -1.0])
        self.roundtrip_simple('f64', 'f64', [0.0, 1.0, -1.0])
        self.roundtrip_simple('char', 'i32', ['a', 'b'])

    def test_resources(self):
        engine = Engine()
        store = Store(engine)
        component = Component(engine, f"""
            (component
                (import "t" (type $t (sub resource)))
                (import "mk" (func $mk (result (own $t))))
                (import "borrow" (func $borrow (param "t" (borrow $t))))
                (import "own" (func $own (param "t" (own $t))))
                (core module $a
                    (import "" "mk" (func $mk (result i32)))
                    (import "" "borrow" (func $borrow (param i32)))
                    (import "" "own" (func $own (param i32)))
                    (import "" "drop" (func $drop (param i32)))

                    (func (export "mk") (result i32) call $mk)
                    (func (export "borrow") (param i32)
                        (call $borrow (local.get 0))
                        (call $drop (local.get 0)))
                    (func (export "own") (param i32) local.get 0 call $own)
                )
                (core func $mk (canon lower (func $mk)))
                (core func $borrow (canon lower (func $borrow)))
                (core func $own (canon lower (func $own)))
                (core func $drop (canon resource.drop $t))
                (core instance $a (instantiate $a
                    (with "" (instance
                        (export "mk" (func $mk))
                        (export "borrow" (func $borrow))
                        (export "own" (func $own))
                        (export "drop" (func $drop))
                    ))
                ))
                (func (export "mk") (result (own $t))
                    (canon lift (core func $a "mk")))
                (func (export "borrow") (param "x" (borrow $t))
                    (canon lift (core func $a "borrow")))
                (func (export "own") (param "x" (own $t))
                    (canon lift (core func $a "own")))
            )
        """)

        ty = ResourceType.host(2)

        def mk(_store):
            return ResourceHost.own(1, 2)

        def borrow(_store, b):
            self.assertFalse(b.owned)
            handle = b.to_host(store)
            self.assertEqual(handle.type, 2)

        def own(_store, b):
            self.assertTrue(b.owned)

        linker = Linker(engine)
        with linker.root() as l:
            l.add_resource('t', ty, lambda _store, _rep: None)
            l.add_func('mk', mk)
            l.add_func('borrow', borrow)
            l.add_func('own', own)
        instance = linker.instantiate(store, component)
        f_mk = instance.get_func(store, 'mk')
        f_borrow = instance.get_func(store, 'borrow')
        f_own = instance.get_func(store, 'own')
        assert(f_mk is not None)
        assert(f_borrow is not None)
        assert(f_own is not None)

        r1 = f_mk(store)
        self.assertIsInstance(r1, ResourceAny)
        f_mk.post_return(store)
        f_borrow(store, r1)
        f_borrow.post_return(store)
        f_borrow(store, ResourceHost.own(1, 2))
        f_borrow.post_return(store)
        f_own(store, r1)
        f_own.post_return(store)
        f_own(store, ResourceHost.own(1, 2))
        f_own.post_return(store)

        with self.assertRaises(TypeError):
            f_borrow(store, 1)

        with self.assertRaises(TypeError):
            f_own(store, 1)


    def test_enum(self):
        self.roundtrip_simple('(enum "a" "b" "c")', 'i32', ['a', 'b', 'c'])
        with self.assertRaises(WasmtimeError):
            self.roundtrip_simple('(enum "a" "b" "c")', 'i32', ['d'])


    def test_flags(self):
        vals = [{'a'}, {'b'}, {'c'}, {'a', 'b'}, {'a', 'c'}, {'b', 'c'}]
        self.roundtrip_simple('(flags "a" "b" "c")', 'i32', vals)
        with self.assertRaises(WasmtimeError):
            self.roundtrip_simple('(flags "a" "b" "c")', 'i32', [{'d'}])


    def test_record(self):
        ty_wit = '(record (field "a" u32) (field "b" bool))'
        ty_wasm = 'i32 i32'
        wat = retptr_component(ty_wit, ty_wasm)
        @dataclass
        class Record:
            a: int
            b: bool
        values = [
                Record(0, False),
                Record(1, True),
                Record(42, False),
                Record(65535, True)
        ]
        self.roundtrip(wat, values, bad = AttributeError)

        @dataclass
        class RecordBad:
            a: int
        with self.assertRaises(AttributeError):
            self.roundtrip(wat, [RecordBad(0)])

    def test_tuple(self):
        ty_wit = '(tuple u32 bool)'
        ty_wasm = 'i32 i32'
        wat = retptr_component(ty_wit, ty_wasm)
        values = [(0, False), (1, True), (42, False), (65535, True)]
        self.roundtrip(wat, values)

        with self.assertRaises(TypeError):
            self.roundtrip(wat, [(0,)])

        with self.assertRaises(TypeError):
            self.roundtrip(wat, [(0, 'x')])

    def test_string(self):
        wat = list_component('string')
        self.roundtrip(wat, ['', 'a', 'hello, world!'])

    def test_list(self):
        wat = list_component('(list u8)')
        self.roundtrip(wat, [b'', b'a', b'hello, world!'])
        wat = list_component('(list u32)')
        self.roundtrip(wat, [[], [1], [1, 2, 3, 4, 5]])
        with self.assertRaises(TypeError):
            self.roundtrip(wat, [[1, 2, 3, 'x']])

    def test_variant(self):
        self.roundtrip_simple('(variant (case "a") (case "b"))',
                              'i32',
                              [Variant('a'), Variant('b')])

        with self.assertRaises(ValueError):
            self.roundtrip_simple('(variant (case "a") (case "b"))',
                                  'i32',
                                  [Variant('c')])

        wat = retptr_component('(variant (case "a" u32) (case "b" u64))', 'i32 i64')
        self.roundtrip(wat, [Variant('a', 1), Variant('b', 2)])

        wat = retptr_component('(variant (case "a" u32) (case "b" f32))', 'i32 i32')
        self.roundtrip(wat, [1, 2.], bad=ValueError)
        wat = retptr_component('(variant (case "a") (case "b" f32))', 'i32 f32')
        self.roundtrip(wat, [None, 2.], bad=ValueError)


    def test_option(self):
        wat = retptr_component('(option u32)', 'i32 i32')
        self.roundtrip(wat, [None, 3, 0], bad=ValueError)


    def test_result(self):
        wat = retptr_component('(result u32 (error f32))', 'i32 i32')
        self.roundtrip(wat, [3, 1.], bad=ValueError)

        wat = retptr_component('(result u32)', 'i32 i32')
        self.roundtrip(wat, [3, None], bad=ValueError)

        wat = retptr_component('(result (error f32))', 'i32 f32')
        self.roundtrip(wat, [3., None], bad=ValueError)

        self.roundtrip_simple('(result)', 'i32', [Variant('ok'), Variant('err')])


    # TODO: roundtrip future
    # TODO: roundtrip stream
    # TODO: roundtrip error-context
    # TODO: typechecking in variants-of-python-types (e.g. `add_classes`)
