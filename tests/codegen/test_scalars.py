from . import bindgen
import math
from wasmtime import Store

module = """
    (component
        (import "host" (instance $i
            (export "roundtrip-u8" (func (param "a" u8) (result u8)))
            (export "roundtrip-s8" (func (param "a" s8) (result s8)))
            (export "roundtrip-u16" (func (param "a" u16) (result u16)))
            (export "roundtrip-s16" (func (param "a" s16) (result s16)))
            (export "roundtrip-u32" (func (param "a" u32) (result u32)))
            (export "roundtrip-s32" (func (param "a" s32) (result s32)))
            (export "roundtrip-u64" (func (param "a" u64) (result u64)))
            (export "roundtrip-s64" (func (param "a" s64) (result s64)))
            (export "roundtrip-float32" (func (param "a" float32) (result float32)))
            (export "roundtrip-float64" (func (param "a" float64) (result float64)))
            (export "roundtrip-char" (func (param "a" char) (result char)))
            (export "roundtrip-bool" (func (param "a" bool) (result bool)))
        ))
        (core module $m
            (import "" "roundtrip-u8" (func $u8 (param i32) (result i32)))
            (import "" "roundtrip-s8" (func $s8 (param i32) (result i32)))
            (import "" "roundtrip-u16" (func $u16 (param i32) (result i32)))
            (import "" "roundtrip-s16" (func $s16 (param i32) (result i32)))
            (import "" "roundtrip-u32" (func $u32 (param i32) (result i32)))
            (import "" "roundtrip-s32" (func $s32 (param i32) (result i32)))
            (import "" "roundtrip-u64" (func $u64 (param i64) (result i64)))
            (import "" "roundtrip-s64" (func $s64 (param i64) (result i64)))

            (import "" "roundtrip-float32" (func $float32 (param f32) (result f32)))
            (import "" "roundtrip-float64" (func $float64 (param f64) (result f64)))

            (import "" "roundtrip-char" (func $char (param i32) (result i32)))
            (import "" "roundtrip-bool" (func $bool (param i32) (result i32)))

            (func (export "roundtrip-u8") (param i32) (result i32)
                local.get 0 call $u8)
            (func (export "roundtrip-s8") (param i32) (result i32)
                local.get 0 call $s8)
            (func (export "roundtrip-u16") (param i32) (result i32)
                local.get 0 call $u16)
            (func (export "roundtrip-s16") (param i32) (result i32)
                local.get 0 call $s16)
            (func (export "roundtrip-u32") (param i32) (result i32)
                local.get 0 call $u32)
            (func (export "roundtrip-s32") (param i32) (result i32)
                local.get 0 call $s32)
            (func (export "roundtrip-u64") (param i64) (result i64)
                local.get 0 call $u64)
            (func (export "roundtrip-s64") (param i64) (result i64)
                local.get 0 call $s64)

            (func (export "roundtrip-float32") (param f32) (result f32)
                local.get 0 call $float32)
            (func (export "roundtrip-float64") (param f64) (result f64)
                local.get 0 call $float64)

            (func (export "roundtrip-char") (param i32) (result i32)
                local.get 0 call $char)
            (func (export "roundtrip-bool") (param i32) (result i32)
                local.get 0 call $bool)
        )
        (core func $u8 (canon lower (func $i "roundtrip-u8")))
        (core func $s8 (canon lower (func $i "roundtrip-s8")))
        (core func $u16 (canon lower (func $i "roundtrip-u16")))
        (core func $s16 (canon lower (func $i "roundtrip-s16")))
        (core func $u32 (canon lower (func $i "roundtrip-u32")))
        (core func $s32 (canon lower (func $i "roundtrip-s32")))
        (core func $u64 (canon lower (func $i "roundtrip-u64")))
        (core func $s64 (canon lower (func $i "roundtrip-s64")))
        (core func $float32 (canon lower (func $i "roundtrip-float32")))
        (core func $float64 (canon lower (func $i "roundtrip-float64")))
        (core func $char (canon lower (func $i "roundtrip-char")))
        (core func $bool (canon lower (func $i "roundtrip-bool")))

        (core instance $i (instantiate $m
            (with "" (instance
                (export "roundtrip-u8" (func $u8))
                (export "roundtrip-s8" (func $s8))
                (export "roundtrip-u16" (func $u16))
                (export "roundtrip-s16" (func $s16))
                (export "roundtrip-u32" (func $u32))
                (export "roundtrip-s32" (func $s32))
                (export "roundtrip-u64" (func $u64))
                (export "roundtrip-s64" (func $s64))
                (export "roundtrip-float32" (func $float32))
                (export "roundtrip-float64" (func $float64))
                (export "roundtrip-char" (func $char))
                (export "roundtrip-bool" (func $bool))
            ))
        ))

        (func (export "roundtrip-u8") (param "a" u8) (result u8)
            (canon lift (core func $i "roundtrip-u8")))
        (func (export "roundtrip-s8") (param "a" s8) (result s8)
            (canon lift (core func $i "roundtrip-s8")))
        (func (export "roundtrip-u16") (param "a" u16) (result u16)
            (canon lift (core func $i "roundtrip-u16")))
        (func (export "roundtrip-s16") (param "a" s16) (result s16)
            (canon lift (core func $i "roundtrip-s16")))
        (func (export "roundtrip-u32") (param "a" u32) (result u32)
            (canon lift (core func $i "roundtrip-u32")))
        (func (export "roundtrip-s32") (param "a" s32) (result s32)
            (canon lift (core func $i "roundtrip-s32")))
        (func (export "roundtrip-u64") (param "a" u64) (result u64)
            (canon lift (core func $i "roundtrip-u64")))
        (func (export "roundtrip-s64") (param "a" s64) (result s64)
            (canon lift (core func $i "roundtrip-s64")))
        (func (export "roundtrip-float32") (param "a" float32) (result float32)
            (canon lift (core func $i "roundtrip-float32")))
        (func (export "roundtrip-float64") (param "a" float64) (result float64)
            (canon lift (core func $i "roundtrip-float64")))
        (func (export "roundtrip-char") (param "a" char) (result char)
            (canon lift (core func $i "roundtrip-char")))
        (func (export "roundtrip-bool") (param "a" bool) (result bool)
            (canon lift (core func $i "roundtrip-bool")))
    )
"""
bindgen('scalars', module)

from .generated.scalars import Root, RootImports, imports


class Host(imports.HostHost):
    def roundtrip_u8(self, val: int) -> int:
        assert val >= 0
        assert val <= (1 << 8) - 1
        return val

    def roundtrip_s8(self, val: int) -> int:
        assert val >= -(1 << (8 - 1))
        assert val <= (1 << (8 - 1)) - 1
        return val

    def roundtrip_u16(self, val: int) -> int:
        assert val >= 0
        assert val <= (1 << 16) - 1
        return val

    def roundtrip_s16(self, val: int) -> int:
        assert val >= -(1 << (16 - 1))
        assert val <= (1 << (16 - 1)) - 1
        return val

    def roundtrip_u32(self, val: int) -> int:
        assert val >= 0
        assert val <= (1 << 32) - 1
        return val

    def roundtrip_s32(self, val: int) -> int:
        assert val >= -(1 << (32 - 1))
        assert val <= (1 << (32 - 1)) - 1
        return val

    def roundtrip_u64(self, val: int) -> int:
        assert val >= 0
        assert val <= (1 << 64) - 1
        return val

    def roundtrip_s64(self, val: int) -> int:
        assert val >= -(1 << (64 - 1))
        assert val <= (1 << (64 - 1)) - 1
        return val

    def roundtrip_float32(self, a: float) -> float:
        return a

    def roundtrip_float64(self, a: float) -> float:
        return a

    def roundtrip_char(self, a: str) -> str:
        return a

    def roundtrip_bool(self, a: bool) -> bool:
        return a


def test_bindings():
    store = Store()
    bindings = Root(store, RootImports(host=Host()))

    assert bindings.roundtrip_u8(store, 0) == 0
    assert bindings.roundtrip_u8(store, (1 << 8) - 1) == (1 << 8) - 1
    assert bindings.roundtrip_u16(store, 0) == 0
    assert bindings.roundtrip_u16(store, (1 << 16) - 1) == (1 << 16) - 1
    assert bindings.roundtrip_u32(store, 0) == 0
    assert bindings.roundtrip_u32(store, (1 << 32) - 1) == (1 << 32) - 1
    assert bindings.roundtrip_u64(store, 0) == 0
    assert bindings.roundtrip_u64(store, (1 << 64) - 1) == (1 << 64) - 1

    assert bindings.roundtrip_s8(store, 0) == 0
    assert bindings.roundtrip_s8(store, (1 << (8 - 1)) - 1) == (1 << (8 - 1)) - 1
    assert bindings.roundtrip_s8(store, -(1 << (8 - 1))) == -(1 << (8 - 1))
    assert bindings.roundtrip_s16(store, 0) == 0
    assert bindings.roundtrip_s16(store, (1 << (16 - 1)) - 1) == (1 << (16 - 1)) - 1
    assert bindings.roundtrip_s16(store, -(1 << (16 - 1))) == -(1 << (16 - 1))
    assert bindings.roundtrip_s32(store, 0) == 0
    assert bindings.roundtrip_s32(store, (1 << (32 - 1)) - 1) == (1 << (32 - 1)) - 1
    assert bindings.roundtrip_s32(store, -(1 << (32 - 1))) == -(1 << (32 - 1))
    assert bindings.roundtrip_s64(store, 0) == 0
    assert bindings.roundtrip_s64(store, (1 << (64 - 1)) - 1) == (1 << (64 - 1)) - 1
    assert bindings.roundtrip_s64(store, -(1 << (64 - 1))) == -(1 << (64 - 1))

    inf = float('inf')
    assert bindings.roundtrip_float32(store, 1.0) == 1.0
    assert bindings.roundtrip_float32(store, inf) == inf
    assert bindings.roundtrip_float32(store, -inf) == -inf
    assert math.isnan(bindings.roundtrip_float32(store, float('nan')))

    assert bindings.roundtrip_float64(store, 1.0) == 1.0
    assert bindings.roundtrip_float64(store, inf) == inf
    assert bindings.roundtrip_float64(store, -inf) == -inf
    assert math.isnan(bindings.roundtrip_float64(store, float('nan')))

    assert bindings.roundtrip_char(store, 'a') == 'a'
    assert bindings.roundtrip_char(store, ' ') == ' '
    assert bindings.roundtrip_char(store, '🚩') == '🚩'

    assert bindings.roundtrip_bool(store, True)
    assert not bindings.roundtrip_bool(store, False)
