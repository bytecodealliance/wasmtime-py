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

            (export "roundtrip-option" (func (param "a" (option float32)) (result (option u8))))
            (export "roundtrip-result" (func
                (param "a" (result u32 (error float32)))
                (result (result float64 (error u8)))
            ))
            (export "roundtrip-enum" (func (param "a" $e1) (result $e1)))
            (export "variant-casts" (func (param "a" $casts) (result $casts)))
            (export "variant-zeros" (func (param "a" $zeros) (result $zeros)))
        ))

        (core module $libc (memory (export "m") 1))
        (core instance $libc (instantiate $libc))

        (core func $r-opt (canon lower (func $i "roundtrip-option") (memory $libc "m")))
        (core func $r-result (canon lower (func $i "roundtrip-result") (memory $libc "m")))
        (core func $r-enum (canon lower (func $i "roundtrip-enum")))
        (core func $v-casts (canon lower (func $i "variant-casts") (memory $libc "m")))
        (core func $v-zeros (canon lower (func $i "variant-zeros") (memory $libc "m")))

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
        )

        (core instance $i (instantiate $m
            (with "libc" (instance $libc))
            (with "" (instance
                (export "r-opt" (func $r-opt))
                (export "r-result" (func $r-result))
                (export "r-enum" (func $r-enum))
                (export "v-casts" (func $v-casts))
                (export "v-zeros" (func $v-zeros))
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
    )
"""
bindgen('variants', module)

from .generated.variants import Variants, VariantsImports, imports, E1, C1A, C2A, C3A, C4A, C5A, C6A, C1B, C2B, C3B, C4B, C5B, C6B, Z1A, Z2A, Z3A, Z4A
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

def test_bindings():
    store = Store()
    bindings = Variants(store, VariantsImports(host=Host()))

    assert bindings.roundtrip_option(store, 1.) == 1
    assert bindings.roundtrip_option(store, None) == None
    assert bindings.roundtrip_option(store, 2.) == 2

    assert bindings.roundtrip_result(store, Ok(2)) == Ok(2)
    assert bindings.roundtrip_result(store, Ok(4)) == Ok(4)
    assert bindings.roundtrip_result(store, Err(5)) == Err(5)

    assert bindings.roundtrip_enum(store, E1.A) == E1.A
    assert bindings.roundtrip_enum(store, E1.B) == E1.B

    a1, a2, a3, a4, a5, a6 = bindings.variant_casts(store, (
        C1A(1),
        C2A(2),
        C3A(3),
        C4A(4),
        C5A(5),
        C6A(6.),
    ))
    assert a1 == C1A(1)
    assert a2 == C2A(2)
    assert a3 == C3A(3)
    assert a4 == C4A(4)
    assert a5 == C5A(5)
    assert a6 == C6A(6.)

    b1, b2, b3, b4, b5, b6 = bindings.variant_casts(store, (
        C1B(1),
        C2B(2),
        C3B(3),
        C4B(4),
        C5B(5),
        C6B(6.),
    ))
    assert b1 == C1B(1)
    assert b2 == C2B(2)
    assert b3 == C3B(3)
    assert b4 == C4B(4)
    assert b5 == C5B(5)
    assert b6 == C6B(6.)

    z1, z2, z3, z4 = bindings.variant_zeros(store, (
        Z1A(1),
        Z2A(2),
        Z3A(3.),
        Z4A(4.),
    ))
    assert z1 == Z1A(1)
    assert z2 == Z2A(2)
    assert z3 == Z3A(3.)
    assert z4 == Z4A(4.)
