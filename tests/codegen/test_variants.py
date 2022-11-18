from . import bindgen
from wasmtime import Store
from typing import Optional

module = """
    (component
        (type $e1 (enum "a" "b"))

        (type $c1 (variant (case "a" s32) (case "b" s64)))
        (type $c2 (variant (case "a" s32) (case "b" float32)))
        (type $c3 (variant (case "a" s32) (case "b" float64)))
        (type $c4 (variant (case "a" s64) (case "b" float32)))
        (type $c5 (variant (case "a" s64) (case "b" float64)))
        (type $c6 (variant (case "a" float32) (case "b" float64)))
        (type $casts (tuple $c1 $c2 $c3 $c4 $c5 $c6))

        (type $z1 (variant (case "a" s32) (case "b")))
        (type $z2 (variant (case "a" s64) (case "b")))
        (type $z3 (variant (case "a" float32) (case "b")))
        (type $z4 (variant (case "a" float64) (case "b")))
        (type $zeros (tuple $z1 $z2 $z3 $z4))

        (type $all-integers (union bool u8 u16 u32 u64 s8 s16 s32 s64))
        (type $all-floats (union float32 float64))
        (type $duplicated-s32 (union s32 s32 s32))
        (type $distinguished (union s32 float32))

        (import "host" (instance $i
            (export "e1" (type (eq $e1)))

            (export "c1" (type (eq $c1)))
            (export "c2" (type (eq $c2)))
            (export "c3" (type (eq $c3)))
            (export "c4" (type (eq $c4)))
            (export "c5" (type (eq $c5)))
            (export "c6" (type (eq $c6)))
            (export "casts" (type (eq $casts)))

            (export "z1" (type (eq $z1)))
            (export "z2" (type (eq $z2)))
            (export "z3" (type (eq $z3)))
            (export "z4" (type (eq $z4)))
            (export "zeros" (type (eq $zeros)))

            (export "all-integers" (type (eq $all-integers)))
            (export "all-floats" (type (eq $all-floats)))
            (export "duplicated-s32" (type (eq $duplicated-s32)))
            (export "distinguished" (type (eq $distinguished)))

            (export "roundtrip-option" (func (param "a" (option float32)) (result (option u8))))
            (export "roundtrip-result" (func
                (param "a" (result u32 (error float32)))
                (result (result float64 (error u8)))
            ))
            (export "roundtrip-enum" (func (param "a" $e1) (result $e1)))
            (export "variant-casts" (func (param "a" $casts) (result $casts)))
            (export "variant-zeros" (func (param "a" $zeros) (result $zeros)))

            (export "add-one-all-integers" (func (param "a" $all-integers) (result $all-integers)))
            (export "add-one-all-floats" (func (param "a" $all-floats) (result $all-floats)))
            (export "add-one-duplicated-s32" (func (param "a" $duplicated-s32) (result $duplicated-s32)))
            (export "add-one-distinguished" (func (param "a" $distinguished) (result $distinguished)))
        ))

        (core module $libc (memory (export "m") 1))
        (core instance $libc (instantiate $libc))

        (core func $r-opt (canon lower (func $i "roundtrip-option") (memory $libc "m")))
        (core func $r-result (canon lower (func $i "roundtrip-result") (memory $libc "m")))
        (core func $r-enum (canon lower (func $i "roundtrip-enum")))
        (core func $v-casts (canon lower (func $i "variant-casts") (memory $libc "m")))
        (core func $v-zeros (canon lower (func $i "variant-zeros") (memory $libc "m")))
        (core func $a-int (canon lower (func $i "add-one-all-integers") (memory $libc "m")))
        (core func $a-float (canon lower (func $i "add-one-all-floats") (memory $libc "m")))
        (core func $a-dup (canon lower (func $i "add-one-duplicated-s32") (memory $libc "m")))
        (core func $a-dist (canon lower (func $i "add-one-distinguished") (memory $libc "m")))

        (core module $m
            (import "libc" "m" (memory 1))
            (import "" "r-opt" (func $r-opt (param i32 f32 i32)))
            (import "" "r-result" (func $r-result (param i32 i32 i32)))
            (import "" "r-enum" (func $r-enum (param i32) (result i32)))
            (import "" "v-casts" (func $v-casts
                (param i32 i64 i32 i32 i32 i64 i32 i64 i32 i64 i32 i64 i32)
            ))
            (import "" "v-zeros" (func $v-zeros
                (param i32 i32 i32 i64 i32 f32 i32 f64 i32)
            ))
            (import "" "a-int" (func $a-int (param i32 i64 i32)))
            (import "" "a-float" (func $a-float (param i32 i64 i32)))
            (import "" "a-dup" (func $a-dup (param i32 i32 i32)))
            (import "" "a-dist" (func $a-dist (param i32 i32 i32)))

            (func (export "r-opt") (param i32 f32) (result i32)
                (call $r-opt (local.get 0) (local.get 1) (i32.const 100))
                i32.const 100)
            (func (export "r-result") (param i32 i32) (result i32)
                (call $r-result (local.get 0) (local.get 1) (i32.const 100))
                i32.const 100)
            (func (export "r-enum") (param i32) (result i32)
                (call $r-enum (local.get 0)))
            (func (export "v-casts")
                (param i32 i64 i32 i32 i32 i64 i32 i64 i32 i64 i32 i64)
                (result i32)
                local.get 0
                local.get 1
                local.get 2
                local.get 3
                local.get 4
                local.get 5
                local.get 6
                local.get 7
                local.get 8
                local.get 9
                local.get 10
                local.get 11
                i32.const 80
                call $v-casts
                i32.const 80)
            (func (export "v-zeros")
                (param i32 i32 i32 i64 i32 f32 i32 f64)
                (result i32)
                local.get 0
                local.get 1
                local.get 2
                local.get 3
                local.get 4
                local.get 5
                local.get 6
                local.get 7
                i32.const 80
                call $v-zeros
                i32.const 80)

            (func (export "a-int") (param i32 i64) (result i32)
                (call $a-int (local.get 0) (local.get 1) (i32.const 80))
                i32.const 80)
            (func (export "a-float") (param i32 i64) (result i32)
                (call $a-float (local.get 0) (local.get 1) (i32.const 80))
                i32.const 80)
            (func (export "a-dup") (param i32 i32) (result i32)
                (call $a-dup (local.get 0) (local.get 1) (i32.const 80))
                i32.const 80)
            (func (export "a-dist") (param i32 i32) (result i32)
                (call $a-dist (local.get 0) (local.get 1) (i32.const 80))
                i32.const 80)
        )

        (core instance $i (instantiate $m
            (with "libc" (instance $libc))
            (with "" (instance
                (export "r-opt" (func $r-opt))
                (export "r-result" (func $r-result))
                (export "r-enum" (func $r-enum))
                (export "v-casts" (func $v-casts))
                (export "v-zeros" (func $v-zeros))
                (export "a-int" (func $a-int))
                (export "a-float" (func $a-float))
                (export "a-dup" (func $a-dup))
                (export "a-dist" (func $a-dist))
            ))
        ))

        (export "e1" (type $e1))

        (export "c1" (type $c1))
        (export "c2" (type $c2))
        (export "c3" (type $c3))
        (export "c4" (type $c4))
        (export "c5" (type $c5))
        (export "c6" (type $c6))
        (export "casts" (type $casts))

        (export "z1" (type $z1))
        (export "z2" (type $z2))
        (export "z3" (type $z3))
        (export "z4" (type $z4))
        (export "zeros" (type $zeros))

        (export "all-integers" (type $all-integers))
        (export "all-floats" (type $all-floats))
        (export "duplicated-s32" (type $duplicated-s32))
        (export "distinguished" (type $distinguished))

        (func (export "roundtrip-option") (param "a" (option float32)) (result (option u8))
            (canon lift (core func $i "r-opt") (memory $libc "m")))
        (func (export "roundtrip-result")
            (param "a" (result u32 (error float32)))
            (result (result float64 (error u8)))
            (canon lift (core func $i "r-result") (memory $libc "m")))
        (func (export "roundtrip-enum") (param "a" $e1) (result $e1)
            (canon lift (core func $i "r-enum")))
        (func (export "variant-casts") (param "a" $casts) (result $casts)
            (canon lift (core func $i "v-casts") (memory $libc "m")))
        (func (export "variant-zeros") (param "a" $zeros) (result $zeros)
            (canon lift (core func $i "v-zeros") (memory $libc "m")))

        (func (export "add-one-all-integers") (param "a" $all-integers) (result $all-integers)
            (canon lift (core func $i "a-int") (memory $libc "m")))
        (func (export "add-one-all-floats") (param "a" $all-floats) (result $all-floats)
            (canon lift (core func $i "a-float") (memory $libc "m")))
        (func (export "add-one-duplicated-s32") (param "a" $duplicated-s32) (result $duplicated-s32)
            (canon lift (core func $i "a-dup") (memory $libc "m")))
        (func (export "add-one-distinguished") (param "a" $distinguished) (result $distinguished)
            (canon lift (core func $i "a-dist") (memory $libc "m")))
    )
"""
bindgen('variants', module)

from .generated.variants import Variants, VariantsImports, imports
from .generated import variants as e
from .generated.variants.imports import host
from .generated.variants.types import Result, Ok, Err


class Host(imports.Host):
    def roundtrip_option(self, a: Optional[float]) -> Optional[int]:
        if a:
            return int(a)
        return None

    def roundtrip_result(self, a: Result[int, float]) -> Result[float, int]:
        if isinstance(a, Ok):
            return Ok(float(a.value))
        return Err(int(a.value))

    def roundtrip_enum(self, a: host.E1) -> host.E1:
        return a

    def variant_casts(self, a: host.Casts) -> host.Casts:
        return a

    def variant_zeros(self, a: host.Zeros) -> host.Zeros:
        return a

    def add_one_all_integers(self, num: host.AllIntegers) -> host.AllIntegers:
        # Bool
        if isinstance(num, host.AllIntegers0):
            assert num.value in (True, False)
            return host.AllIntegers0(not num.value)
        # The unsigned numbers
        elif isinstance(num, host.AllIntegers1):
            lower_limit = 0
            upper_limit = 2**8
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers1((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegers2):
            lower_limit = 0
            upper_limit = 2**16
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers2((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegers3):
            lower_limit = 0
            upper_limit = 2**32
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers3((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegers4):
            lower_limit = 0
            upper_limit = 2**64
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers4((num.value + 1) % upper_limit)
        # The signed numbers
        elif isinstance(num, host.AllIntegers5):
            lower_limit = -2**7
            upper_limit = 2**7
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers5(num.value + 1)
        elif isinstance(num, host.AllIntegers6):
            lower_limit = -2**15
            upper_limit = 2**15
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers6(num.value + 1)
        elif isinstance(num, host.AllIntegers7):
            lower_limit = -2**31
            upper_limit = 2**31
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers7(num.value + 1)
        elif isinstance(num, host.AllIntegers8):
            lower_limit = -2**63
            upper_limit = 2**63
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegers8(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_all_floats(self, num: host.AllFloats) -> host.AllFloats:
        if isinstance(num, host.AllFloats0):
            return host.AllFloats0(num.value + 1)
        if isinstance(num, host.AllFloats1):
            return host.AllFloats1(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_duplicated_s32(self, num: host.DuplicatedS32) -> host.DuplicatedS32:
        if isinstance(num, host.DuplicatedS320):
            return host.DuplicatedS320(num.value + 1)
        if isinstance(num, host.DuplicatedS321):
            return host.DuplicatedS321(num.value + 1)
        if isinstance(num, host.DuplicatedS322):
            return host.DuplicatedS322(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_distinguished(self, a: host.Distinguished) -> host.Distinguished:
        return a + 1


def test_bindings():
    store = Store()
    wasm = Variants(store, VariantsImports(host=Host()))

    assert wasm.roundtrip_option(store, 1.) == 1
    assert wasm.roundtrip_option(store, None) is None
    assert wasm.roundtrip_option(store, 2.) == 2

    assert wasm.roundtrip_result(store, Ok(2)) == Ok(2)
    assert wasm.roundtrip_result(store, Ok(4)) == Ok(4)
    assert wasm.roundtrip_result(store, Err(5)) == Err(5)

    assert wasm.roundtrip_enum(store, e.E1.A) == e.E1.A
    assert wasm.roundtrip_enum(store, e.E1.B) == e.E1.B

    a1, a2, a3, a4, a5, a6 = wasm.variant_casts(store, (
        e.C1A(1),
        e.C2A(2),
        e.C3A(3),
        e.C4A(4),
        e.C5A(5),
        e.C6A(6.),
    ))
    assert a1 == e.C1A(1)
    assert a2 == e.C2A(2)
    assert a3 == e.C3A(3)
    assert a4 == e.C4A(4)
    assert a5 == e.C5A(5)
    assert a6 == e.C6A(6.)

    b1, b2, b3, b4, b5, b6 = wasm.variant_casts(store, (
        e.C1B(1),
        e.C2B(2),
        e.C3B(3),
        e.C4B(4),
        e.C5B(5),
        e.C6B(6.),
    ))
    assert b1 == e.C1B(1)
    assert b2 == e.C2B(2)
    assert b3 == e.C3B(3)
    assert b4 == e.C4B(4)
    assert b5 == e.C5B(5)
    assert b6 == e.C6B(6.)

    z1, z2, z3, z4 = wasm.variant_zeros(store, (
        e.Z1A(1),
        e.Z2A(2),
        e.Z3A(3.),
        e.Z4A(4.),
    ))
    assert z1 == e.Z1A(1)
    assert z2 == e.Z2A(2)
    assert z3 == e.Z3A(3.)
    assert z4 == e.Z4A(4.)

    # All-Integers
    # Booleans
    assert wasm.add_one_all_integers(store, e.AllIntegers0(False)) == e.AllIntegers0(True)
    assert wasm.add_one_all_integers(store, e.AllIntegers0(True)) == e.AllIntegers0(False)
    # Unsigned integers
    assert wasm.add_one_all_integers(store, e.AllIntegers1(0)) == e.AllIntegers1(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers1(2**8 - 1)) == e.AllIntegers1(0)
    assert wasm.add_one_all_integers(store, e.AllIntegers2(0)) == e.AllIntegers2(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers2(2**16 - 1)) == e.AllIntegers2(0)
    assert wasm.add_one_all_integers(store, e.AllIntegers3(0)) == e.AllIntegers3(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers3(2**32 - 1)) == e.AllIntegers3(0)
    assert wasm.add_one_all_integers(store, e.AllIntegers4(0)) == e.AllIntegers4(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers4(2**64 - 1)) == e.AllIntegers4(0)
    # Signed integers
    assert wasm.add_one_all_integers(store, e.AllIntegers5(0)) == e.AllIntegers5(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers5(2**7 - 2)) == e.AllIntegers5(2**7 - 1)
    assert wasm.add_one_all_integers(store, e.AllIntegers5(-8)) == e.AllIntegers5(-7)
    assert wasm.add_one_all_integers(store, e.AllIntegers6(0)) == e.AllIntegers6(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers6(2**15 - 2)) == e.AllIntegers6(2**15 - 1)
    assert wasm.add_one_all_integers(store, e.AllIntegers6(-8)) == e.AllIntegers6(-7)
    assert wasm.add_one_all_integers(store, e.AllIntegers7(0)) == e.AllIntegers7(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers7(2**31 - 2)) == e.AllIntegers7(2**31 - 1)
    assert wasm.add_one_all_integers(store, e.AllIntegers7(-8)) == e.AllIntegers7(-7)
    assert wasm.add_one_all_integers(store, e.AllIntegers8(0)) == e.AllIntegers8(1)
    assert wasm.add_one_all_integers(store, e.AllIntegers8(2**63 - 2)) == e.AllIntegers8(2**63 - 1)
    assert wasm.add_one_all_integers(store, e.AllIntegers8(-8)) == e.AllIntegers8(-7)

    assert wasm.add_one_all_floats(store, e.AllFloats0(0.0)) == e.AllFloats0(1.0)
    assert wasm.add_one_all_floats(store, e.AllFloats1(0.0)) == e.AllFloats1(1.0)

    assert wasm.add_one_duplicated_s32(store, e.DuplicatedS320(0)) == e.DuplicatedS320(1)
    assert wasm.add_one_duplicated_s32(store, e.DuplicatedS321(1)) == e.DuplicatedS321(2)
    assert wasm.add_one_duplicated_s32(store, e.DuplicatedS322(2)) == e.DuplicatedS322(3)

    assert wasm.add_one_distinguished(store, 1) == 2
    assert wasm.add_one_distinguished(store, 2.) == 3.
