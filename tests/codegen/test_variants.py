from . import bindgen
from wasmtime import Store
from typing import Optional

module = """
    (component
        (import "host" (instance $i
            (type $e1 (enum "a" "b"))

            (type $c1 (variant (case "a" s32) (case "b" s64)))
            (type $c2 (variant (case "a" s32) (case "b" float32)))
            (type $c3 (variant (case "a" s32) (case "b" float64)))
            (type $c4 (variant (case "a" s64) (case "b" float32)))
            (type $c5 (variant (case "a" s64) (case "b" float64)))
            (type $c6 (variant (case "a" float32) (case "b" float64)))

            (type $z1 (variant (case "a" s32) (case "b")))
            (type $z2 (variant (case "a" s64) (case "b")))
            (type $z3 (variant (case "a" float32) (case "b")))
            (type $z4 (variant (case "a" float64) (case "b")))

            (type $all-integers (variant
                (case "bool" bool)
                (case "u8" u8)
                (case "u16" u16)
                (case "u32" u32)
                (case "u64" u64)
                (case "s8" s8)
                (case "s16" s16)
                (case "s32" s32)
                (case "s64" s64)
            ))
            (type $all-floats (variant (case "f32" float32) (case "f64" float64)))
            (type $duplicated-s32 (variant
                (case "c1" s32)
                (case "c2" s32)
                (case "c3" s32)
            ))
            (type $distinguished (variant (case "s32" s32) (case "float32" float32)))
            (export $distinguished' "distinguished" (type (eq $distinguished)))

            (type $nested-union (variant
                (case "d" $distinguished')
                (case "s32" s32)
                (case "float32" float32)
            ))
            (type $option-in-union (variant (case "o" (option s32)) (case "i" s32)))

            (export $e1' "e1" (type (eq $e1)))

            (export $c1' "c1" (type (eq $c1)))
            (export $c2' "c2" (type (eq $c2)))
            (export $c3' "c3" (type (eq $c3)))
            (export $c4' "c4" (type (eq $c4)))
            (export $c5' "c5" (type (eq $c5)))
            (export $c6' "c6" (type (eq $c6)))
            (type $casts (tuple $c1' $c2' $c3' $c4' $c5' $c6'))
            (export $casts' "casts" (type (eq $casts)))

            (export $z1' "z1" (type (eq $z1)))
            (export $z2' "z2" (type (eq $z2)))
            (export $z3' "z3" (type (eq $z3)))
            (export $z4' "z4" (type (eq $z4)))
            (type $zeros (tuple $z1' $z2' $z3' $z4'))
            (export $zeros' "zeros" (type (eq $zeros)))

            (export $all-integers' "all-integers" (type (eq $all-integers)))
            (export $all-floats' "all-floats" (type (eq $all-floats)))
            (export $duplicated-s32' "duplicated-s32" (type (eq $duplicated-s32)))
            (export $nested-union' "nested-union" (type (eq $nested-union)))
            (export $option-in-union' "option-in-union" (type (eq $option-in-union)))

            (export "roundtrip-option" (func (param "a" (option float32)) (result (option u8))))
            (export "roundtrip-result" (func
                (param "a" (result u32 (error float32)))
                (result (result float64 (error u8)))
            ))
            (export "roundtrip-enum" (func (param "a" $e1') (result $e1')))
            (export "variant-casts" (func (param "a" $casts') (result $casts')))
            (export "variant-zeros" (func (param "a" $zeros') (result $zeros')))

            (export "add-one-all-integers" (func (param "a" $all-integers') (result $all-integers')))
            (export "add-one-all-floats" (func (param "a" $all-floats') (result $all-floats')))
            (export "add-one-duplicated-s32" (func (param "a" $duplicated-s32') (result $duplicated-s32')))
            (export "add-one-distinguished" (func (param "a" $distinguished') (result $distinguished')))
            (export "add-one-nested-union" (func (param "a" $nested-union') (result $nested-union')))
            (export "add-one-option-in-union" (func (param "a" $option-in-union') (result $option-in-union')))
            (export "add-one-option-in-option" (func (param "a" (option (option s32))) (result (option (option s32)))))
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
        (core func $a-nest (canon lower (func $i "add-one-nested-union") (memory $libc "m")))
        (core func $a-oinu (canon lower (func $i "add-one-option-in-union") (memory $libc "m")))
        (core func $a-oino (canon lower (func $i "add-one-option-in-option") (memory $libc "m")))

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
            (import "" "a-nest" (func $a-nest (param i32 i32 i32 i32)))
            (import "" "a-oinu" (func $a-oinu (param i32 i32 i32 i32)))
            (import "" "a-oino" (func $a-oino (param i32 i32 i32 i32)))

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
            (func (export "a-nest") (param i32 i32 i32) (result i32)
                (call $a-nest (local.get 0) (local.get 1) (local.get 2) (i32.const 80))
                i32.const 80)
            (func (export "a-oinu") (param i32 i32 i32) (result i32)
                (call $a-oinu (local.get 0) (local.get 1) (local.get 2) (i32.const 80))
                i32.const 80)
            (func (export "a-oino") (param i32 i32 i32) (result i32)
                (call $a-oino (local.get 0) (local.get 1) (local.get 2) (i32.const 80))
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
                (export "a-nest" (func $a-nest))
                (export "a-oinu" (func $a-oinu))
                (export "a-oino" (func $a-oino))
            ))
        ))

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

        (type $all-integers (variant
            (case "bool" bool)
            (case "u8" u8)
            (case "u16" u16)
            (case "u32" u32)
            (case "u64" u64)
            (case "s8" s8)
            (case "s16" s16)
            (case "s32" s32)
            (case "s64" s64)
        ))
        (type $all-floats (variant (case "f32" float32) (case "f64" float64)))
        (type $duplicated-s32 (variant
            (case "c1" s32)
            (case "c2" s32)
            (case "c3" s32)
        ))
        (type $distinguished (variant (case "s32" s32) (case "float32" float32)))
        (type $nested-union (variant
            (case "d" $distinguished)
            (case "s32" s32)
            (case "float32" float32)
        ))
        (type $option-in-union (variant (case "o" (option s32)) (case "i" s32)))

        (func $roundtrip-option (param "a" (option float32)) (result (option u8))
            (canon lift (core func $i "r-opt") (memory $libc "m")))
        (func $roundtrip-result
            (param "a" (result u32 (error float32)))
            (result (result float64 (error u8)))
            (canon lift (core func $i "r-result") (memory $libc "m")))
        (func $roundtrip-enum (param "a" $e1) (result $e1)
            (canon lift (core func $i "r-enum")))
        (func $variant-casts (param "a" $casts) (result $casts)
            (canon lift (core func $i "v-casts") (memory $libc "m")))
        (func $variant-zeros (param "a" $zeros) (result $zeros)
            (canon lift (core func $i "v-zeros") (memory $libc "m")))

        (func $add-one-all-integers (param "a" $all-integers) (result $all-integers)
            (canon lift (core func $i "a-int") (memory $libc "m")))
        (func $add-one-all-floats (param "a" $all-floats) (result $all-floats)
            (canon lift (core func $i "a-float") (memory $libc "m")))
        (func $add-one-duplicated-s32 (param "a" $duplicated-s32) (result $duplicated-s32)
            (canon lift (core func $i "a-dup") (memory $libc "m")))
        (func $add-one-distinguished (param "a" $distinguished) (result $distinguished)
            (canon lift (core func $i "a-dist") (memory $libc "m")))
        (func $add-one-nested-union (param "a" $nested-union) (result $nested-union)
            (canon lift (core func $i "a-nest") (memory $libc "m")))
        (func $add-one-option-in-union (param "a" $option-in-union) (result $option-in-union)
            (canon lift (core func $i "a-oinu") (memory $libc "m")))
        (func $add-one-option-in-option (param "a" (option (option s32))) (result (option (option s32)))
            (canon lift (core func $i "a-oino") (memory $libc "m")))

        (instance (export "e")
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
            (export "nested-union" (type $nested-union))
            (export "option-in-union" (type $option-in-union))

            (export "roundtrip-option" (func $roundtrip-option))
            (export "roundtrip-result" (func $roundtrip-result))
            (export "roundtrip-enum" (func $roundtrip-enum))
            (export "variant-casts" (func $variant-casts))
            (export "variant-zeros" (func $variant-zeros))
            (export "add-one-all-integers" (func $add-one-all-integers))
            (export "add-one-all-floats" (func $add-one-all-floats))
            (export "add-one-duplicated-s32" (func $add-one-duplicated-s32))
            (export "add-one-distinguished" (func $add-one-distinguished))
            (export "add-one-nested-union" (func $add-one-nested-union))
            (export "add-one-option-in-union" (func $add-one-option-in-union))
            (export "add-one-option-in-option" (func $add-one-option-in-option))
        )
    )
"""
bindgen('variants', module)

from .generated.variants import Root, RootImports, imports
from .generated.variants import e
from .generated.variants.imports import host
from .generated.variants.types import Result, Ok, Err, Some


class Host(imports.HostHost):
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
        if isinstance(num, host.AllIntegersBool):
            assert num.value in (True, False)
            return host.AllIntegersBool(not num.value)
        # The unsigned numbers
        elif isinstance(num, host.AllIntegersU8):
            lower_limit = 0
            upper_limit = 2**8
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersU8((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegersU16):
            lower_limit = 0
            upper_limit = 2**16
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersU16((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegersU32):
            lower_limit = 0
            upper_limit = 2**32
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersU32((num.value + 1) % upper_limit)
        elif isinstance(num, host.AllIntegersU64):
            lower_limit = 0
            upper_limit = 2**64
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersU64((num.value + 1) % upper_limit)
        # The signed numbers
        elif isinstance(num, host.AllIntegersS8):
            lower_limit = -2**7
            upper_limit = 2**7
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersS8(num.value + 1)
        elif isinstance(num, host.AllIntegersS16):
            lower_limit = -2**15
            upper_limit = 2**15
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersS16(num.value + 1)
        elif isinstance(num, host.AllIntegersS32):
            lower_limit = -2**31
            upper_limit = 2**31
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersS32(num.value + 1)
        elif isinstance(num, host.AllIntegersS64):
            lower_limit = -2**63
            upper_limit = 2**63
            assert lower_limit <= num.value < upper_limit
            return host.AllIntegersS64(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_all_floats(self, num: host.AllFloats) -> host.AllFloats:
        if isinstance(num, host.AllFloatsF32):
            return host.AllFloatsF32(num.value + 1)
        if isinstance(num, host.AllFloatsF64):
            return host.AllFloatsF64(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_duplicated_s32(self, num: host.DuplicatedS32) -> host.DuplicatedS32:
        if isinstance(num, host.DuplicatedS32C1):
            return host.DuplicatedS32C1(num.value + 1)
        if isinstance(num, host.DuplicatedS32C2):
            return host.DuplicatedS32C2(num.value + 1)
        if isinstance(num, host.DuplicatedS32C3):
            return host.DuplicatedS32C3(num.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_distinguished(self, a: host.Distinguished) -> host.Distinguished:
        a.value += 1
        return a

    def add_one_nested_union(self, a: host.NestedUnion) -> host.NestedUnion:
        if isinstance(a, host.NestedUnionD):
            a.value.value += 1
            return host.NestedUnionD(a.value)
        if isinstance(a, host.NestedUnionS32):
            return host.NestedUnionS32(a.value + 1)
        if isinstance(a, host.NestedUnionFloat32):
            return host.NestedUnionFloat32(a.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_option_in_union(self, a: host.OptionInUnion) -> host.OptionInUnion:
        if isinstance(a, host.OptionInUnionO):
            if a.value is None:
                return host.OptionInUnionO(None)
            else:
                return host.OptionInUnionO(a.value + 1)
        if isinstance(a, host.OptionInUnionI):
            return host.OptionInUnionI(a.value + 1)
        else:
            raise ValueError("Invalid input value!")

    def add_one_option_in_option(self, a: Optional[Some[Optional[int]]]) -> Optional[Some[Optional[int]]]:
        if isinstance(a, Some):
            if a.value is None:
                return Some(None)
            else:
                return Some(a.value + 1)
        if a is None:
            return None
        else:
            raise ValueError("Invalid input value!")


def test_bindings():
    store = Store()
    wasm = Root(store, RootImports(host=Host()))

    exports = wasm.e()
    assert exports.roundtrip_option(store, 1.) == 1
    assert exports.roundtrip_option(store, None) is None
    assert exports.roundtrip_option(store, 2.) == 2

    assert exports.roundtrip_result(store, Ok(2)) == Ok(2)
    assert exports.roundtrip_result(store, Ok(4)) == Ok(4)
    assert exports.roundtrip_result(store, Err(5)) == Err(5)

    assert exports.roundtrip_enum(store, e.E1.A) == e.E1.A
    assert exports.roundtrip_enum(store, e.E1.B) == e.E1.B

    a1, a2, a3, a4, a5, a6 = exports.variant_casts(store, (
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

    b1, b2, b3, b4, b5, b6 = exports.variant_casts(store, (
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

    z1, z2, z3, z4 = exports.variant_zeros(store, (
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
    assert exports.add_one_all_integers(store, e.AllIntegersBool(False)) == e.AllIntegersBool(True)
    assert exports.add_one_all_integers(store, e.AllIntegersBool(True)) == e.AllIntegersBool(False)
    # Unsigned integers
    assert exports.add_one_all_integers(store, e.AllIntegersU8(0)) == e.AllIntegersU8(1)
    assert exports.add_one_all_integers(store, e.AllIntegersU8(2**8 - 1)) == e.AllIntegersU8(0)
    assert exports.add_one_all_integers(store, e.AllIntegersU16(0)) == e.AllIntegersU16(1)
    assert exports.add_one_all_integers(store, e.AllIntegersU16(2**16 - 1)) == e.AllIntegersU16(0)
    assert exports.add_one_all_integers(store, e.AllIntegersU32(0)) == e.AllIntegersU32(1)
    assert exports.add_one_all_integers(store, e.AllIntegersU32(2**32 - 1)) == e.AllIntegersU32(0)
    assert exports.add_one_all_integers(store, e.AllIntegersU64(0)) == e.AllIntegersU64(1)
    assert exports.add_one_all_integers(store, e.AllIntegersU64(2**64 - 1)) == e.AllIntegersU64(0)
    # Signed integers
    assert exports.add_one_all_integers(store, e.AllIntegersS8(0)) == e.AllIntegersS8(1)
    assert exports.add_one_all_integers(store, e.AllIntegersS8(2**7 - 2)) == e.AllIntegersS8(2**7 - 1)
    assert exports.add_one_all_integers(store, e.AllIntegersS8(-8)) == e.AllIntegersS8(-7)
    assert exports.add_one_all_integers(store, e.AllIntegersS16(0)) == e.AllIntegersS16(1)
    assert exports.add_one_all_integers(store, e.AllIntegersS16(2**15 - 2)) == e.AllIntegersS16(2**15 - 1)
    assert exports.add_one_all_integers(store, e.AllIntegersS16(-8)) == e.AllIntegersS16(-7)
    assert exports.add_one_all_integers(store, e.AllIntegersS32(0)) == e.AllIntegersS32(1)
    assert exports.add_one_all_integers(store, e.AllIntegersS32(2**31 - 2)) == e.AllIntegersS32(2**31 - 1)
    assert exports.add_one_all_integers(store, e.AllIntegersS32(-8)) == e.AllIntegersS32(-7)
    assert exports.add_one_all_integers(store, e.AllIntegersS64(0)) == e.AllIntegersS64(1)
    assert exports.add_one_all_integers(store, e.AllIntegersS64(2**63 - 2)) == e.AllIntegersS64(2**63 - 1)
    assert exports.add_one_all_integers(store, e.AllIntegersS64(-8)) == e.AllIntegersS64(-7)

    assert exports.add_one_all_floats(store, e.AllFloatsF32(0.0)) == e.AllFloatsF32(1.0)
    assert exports.add_one_all_floats(store, e.AllFloatsF64(0.0)) == e.AllFloatsF64(1.0)

    assert exports.add_one_duplicated_s32(store, e.DuplicatedS32C1(0)) == e.DuplicatedS32C1(1)
    assert exports.add_one_duplicated_s32(store, e.DuplicatedS32C2(1)) == e.DuplicatedS32C2(2)
    assert exports.add_one_duplicated_s32(store, e.DuplicatedS32C3(2)) == e.DuplicatedS32C3(3)

    assert exports.add_one_distinguished(store, e.DistinguishedS32(1)) == e.DistinguishedS32(2)
    assert exports.add_one_distinguished(store, e.DistinguishedFloat32(2.)) == e.DistinguishedFloat32(3.)

    assert exports.add_one_nested_union(store, e.NestedUnionD(e.DistinguishedS32(1))) == e.NestedUnionD(e.DistinguishedS32(2))
    assert exports.add_one_nested_union(store, e.NestedUnionD(e.DistinguishedFloat32(2.))) == e.NestedUnionD(e.DistinguishedFloat32(3.))
    assert exports.add_one_nested_union(store, e.NestedUnionS32(3)) == e.NestedUnionS32(4)
    assert exports.add_one_nested_union(store, e.NestedUnionFloat32(4.)) == e.NestedUnionFloat32(5.)

    assert exports.add_one_option_in_union(store, e.OptionInUnionO(1)) == e.OptionInUnionO(2)
    assert exports.add_one_option_in_union(store, e.OptionInUnionO(None)) == e.OptionInUnionO(None)
    assert exports.add_one_option_in_union(store, e.OptionInUnionI(1)) == e.OptionInUnionI(2)

    assert exports.add_one_option_in_option(store, Some(1)) == Some(2)
    assert exports.add_one_option_in_option(store, Some(None)) == Some(None)
    assert exports.add_one_option_in_option(store, None) is None
