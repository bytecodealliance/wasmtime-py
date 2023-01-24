from . import bindgen
from typing import Tuple
from wasmtime import Store

module = """
    (component
        (type $tuple (tuple u8 u32))

        (type $flag1 (flags "a" "b"))
        (type $flag2 (flags "a" "b" "c"))
        (type $flag8 (flags "a1" "a2" "a3" "a4" "a5" "a6" "a7" "a8"))
        (type $flag16 (flags
            "a1" "a2" "a3" "a4" "a5" "a6" "a7" "a8" "a9" "a10" "a11" "a12" "a13"
            "a14" "a15" "a16"
        ))
        (type $flag32 (flags
            "a1" "a2" "a3" "a4" "a5" "a6" "a7" "a8" "a9" "a10" "a11" "a12" "a13"
            "a14" "a15" "a16" "a17" "a18" "a19" "a20" "a21" "a22" "a23" "a24"
            "a25" "a26" "a27" "a28" "a29" "a30" "a31" "a32"
        ))
        (type $flag64 (flags
            "a1" "a2" "a3" "a4" "a5" "a6" "a7" "a8" "a9" "a10" "a11" "a12" "a13"
            "a14" "a15" "a16" "a17" "a18" "a19" "a20" "a21" "a22" "a23" "a24"
            "a25" "a26" "a27" "a28" "a29" "a30" "a31" "a32" "a33" "a34" "a35"
            "a36" "a37" "a38" "a39" "a40" "a41" "a42" "a43" "a44" "a45" "a46"
            "a47" "a48" "a49" "a50" "a51" "a52" "a53" "a54" "a55" "a56" "a57"
            "a58" "a59" "a60" "a61" "a62" "a63" "a64"
        ))

        (type $r1 (record (field "a" u8) (field "b" $flag1)))

        (import "host" (instance $i
            (export "multiple-results" (func (result "a" u8) (result "b" u16)))
            (export "swap" (func (param "a" $tuple) (result $tuple)))

            (export $f1 "flag1" (type (eq $flag1)))
            (export $f2 "flag2" (type (eq $flag2)))
            (export $f8 "flag8" (type (eq $flag8)))
            (export $f16 "flag16" (type (eq $flag16)))
            (export $f32 "flag32" (type (eq $flag32)))
            (export $f64 "flag64" (type (eq $flag64)))

            (export "roundtrip-flag1" (func (param "a" $f1) (result $f1)))
            (export "roundtrip-flag2" (func (param "a" $f2) (result $f2)))
            (export "roundtrip-flag8" (func (param "a" $f8) (result $f8)))
            (export "roundtrip-flag16" (func (param "a" $f16) (result $f16)))
            (export "roundtrip-flag32" (func (param "a" $f32) (result $f32)))
            (export "roundtrip-flag64" (func (param "a" $f64) (result $f64)))

            (export "empty-tuple" (func (param "a" (tuple)) (result (tuple))))

            (type $r1 (record (field "a" u8) (field "b" $f1)))
            (export $r1' "r1" (type (eq $r1)))
            (export "roundtrip-r1" (func (param "a" $r1') (result $r1')))
        ))

        (core module $libc
            (memory (export "mem") 1)
        )
        (core instance $libc (instantiate $libc))

        (core func $multi (canon lower (func $i "multiple-results") (memory $libc "mem")))
        (core func $swap (canon lower (func $i "swap") (memory $libc "mem")))
        (core func $r-flag1 (canon lower (func $i "roundtrip-flag1")))
        (core func $r-flag2 (canon lower (func $i "roundtrip-flag2")))
        (core func $r-flag8 (canon lower (func $i "roundtrip-flag8")))
        (core func $r-flag16 (canon lower (func $i "roundtrip-flag16")))
        (core func $r-flag32 (canon lower (func $i "roundtrip-flag32")))
        (core func $r-flag64 (canon lower (func $i "roundtrip-flag64") (memory $libc "mem")))
        (core func $r-empty (canon lower (func $i "empty-tuple")))
        (core func $r-r1 (canon lower (func $i "roundtrip-r1") (memory $libc "mem")))

        (core module $m
            (import "" "r-flag1" (func $r-flag1 (param i32) (result i32)))
            (import "" "r-flag2" (func $r-flag2 (param i32) (result i32)))
            (import "" "r-flag8" (func $r-flag8 (param i32) (result i32)))
            (import "" "r-flag16" (func $r-flag16 (param i32) (result i32)))
            (import "" "r-flag32" (func $r-flag32 (param i32) (result i32)))
            (import "" "r-flag64" (func $r-flag64 (param i32 i32 i32)))
            (import "" "multi" (func $multi (param i32)))
            (import "" "swap" (func $swap (param i32 i32 i32)))
            (import "" "r-empty" (func $r-empty))
            (import "" "r-r1" (func $r-r1 (param i32 i32 i32)))

            (import "libc" "mem" (memory 1))

            (func (export "multi") (result i32)
                (call $multi (i32.const 100))
                i32.const 100)

            (func (export "swap") (param i32 i32) (result i32)
                (call $swap (local.get 0) (local.get 1) (i32.const 100))
                i32.const 100)

            (func (export "r-flag1") (param i32) (result i32)
                (call $r-flag1 (local.get 0)))
            (func (export "r-flag2") (param i32) (result i32)
                (call $r-flag2 (local.get 0)))
            (func (export "r-flag8") (param i32) (result i32)
                (call $r-flag8 (local.get 0)))
            (func (export "r-flag16") (param i32) (result i32)
                (call $r-flag16 (local.get 0)))
            (func (export "r-flag32") (param i32) (result i32)
                (call $r-flag32 (local.get 0)))
            (func (export "r-flag64") (param i32 i32) (result i32)
                (call $r-flag64 (local.get 0) (local.get 1) (i32.const 100))
                i32.const 100)
            (func (export "r-empty") (call $r-empty))
            (func (export "r-r1") (param i32 i32) (result i32)
                (call $r-r1 (local.get 0) (local.get 1) (i32.const 100))
                i32.const 100)
        )

        (core instance $i (instantiate $m
            (with "libc" (instance $libc))
            (with "" (instance
                (export "multi" (func $multi))
                (export "swap" (func $swap))
                (export "r-flag1" (func $r-flag1))
                (export "r-flag2" (func $r-flag2))
                (export "r-flag8" (func $r-flag8))
                (export "r-flag16" (func $r-flag16))
                (export "r-flag32" (func $r-flag32))
                (export "r-flag64" (func $r-flag64))
                (export "r-empty" (func $r-empty))
                (export "r-r1" (func $r-r1))
            ))
        ))

        (func $multiple-results (result "a" u8) (result "b" u16)
            (canon lift (core func $i "multi") (memory $libc "mem")))
        (func $swap (param "a" $tuple) (result "a" $tuple)
            (canon lift (core func $i "swap") (memory $libc "mem")))
        (func $roundtrip-flag1 (param "a" $flag1) (result "a" $flag1)
            (canon lift (core func $i "r-flag1")))
        (func $roundtrip-flag2  (param "a" $flag2) (result "a" $flag2)
            (canon lift (core func $i "r-flag2")))
        (func $roundtrip-flag8 (param "a" $flag8) (result "a" $flag8)
            (canon lift (core func $i "r-flag8")))
        (func $roundtrip-flag16 (param "a" $flag16) (result "a" $flag16)
            (canon lift (core func $i "r-flag16")))
        (func $roundtrip-flag32 (param "a" $flag32) (result "a" $flag32)
            (canon lift (core func $i "r-flag32")))
        (func $roundtrip-flag64 (param "a" $flag64) (result "a" $flag64)
            (canon lift (core func $i "r-flag64") (memory $libc "mem")))
        (func $empty-tuple (param "a" (tuple)) (result "a" (tuple))
            (canon lift (core func $i "r-empty")))
        (func $roundtrip-r1 (param "a" $r1) (result "b" $r1)
            (canon lift (core func $i "r-r1") (memory $libc "mem")))

        (instance (export "e")
            (export "flag1" (type $flag1))
            (export "flag2" (type $flag2))
            (export "flag8" (type $flag8))
            (export "flag16" (type $flag16))
            (export "flag32" (type $flag32))
            (export "flag64" (type $flag64))
            (export "r1" (type $r1))

            (export "multiple-results" (func $multiple-results))
            (export "swap" (func $swap))
            (export "roundtrip-flag1" (func $roundtrip-flag1))
            (export "roundtrip-flag2" (func $roundtrip-flag2))
            (export "roundtrip-flag8" (func $roundtrip-flag8))
            (export "roundtrip-flag16" (func $roundtrip-flag16))
            (export "roundtrip-flag32" (func $roundtrip-flag32))
            (export "roundtrip-flag64" (func $roundtrip-flag64))
            (export "empty-tuple" (func $empty-tuple))
            (export "roundtrip-r1" (func $roundtrip-r1))
        )
    )
"""
bindgen('records', module)

from .generated.records import Records, RecordsImports, imports
from .generated.records.exports.e import Flag1, Flag2, Flag8, Flag16, Flag32, Flag64, R1
from .generated.records.imports import host


class Host(imports.Host):
    def multiple_results(self) -> Tuple[int, int]:
        return 1, 2

    def swap(self, tuple: Tuple[int, int]) -> Tuple[int, int]:
        a, b = tuple
        return b, a

    def roundtrip_flag1(self, f: host.Flag1) -> host.Flag1:
        return f

    def roundtrip_flag2(self, f: host.Flag2) -> host.Flag2:
        return f

    def roundtrip_flag8(self, f: host.Flag8) -> host.Flag8:
        return f

    def roundtrip_flag16(self, f: host.Flag16) -> host.Flag16:
        return f

    def roundtrip_flag32(self, f: host.Flag32) -> host.Flag32:
        return f

    def roundtrip_flag64(self, f: host.Flag64) -> host.Flag64:
        return f

    def empty_tuple(self, f: None) -> None:
        return f

    def roundtrip_r1(self, f: host.R1) -> host.R1:
        return f


def test_bindings():
    store = Store()
    bindings = Records(store, RecordsImports(host=Host()))

    assert bindings.e().multiple_results(store) == (1, 2)
    assert bindings.e().swap(store, (3, 4)) == (4, 3)

    assert bindings.e().roundtrip_flag1(store, Flag1(0)) == Flag1(0)
    for f1 in Flag1:
        assert bindings.e().roundtrip_flag1(store, f1) == f1
    assert bindings.e().roundtrip_flag2(store, Flag2(0)) == Flag2(0)
    for f2 in Flag2:
        assert bindings.e().roundtrip_flag2(store, f2) == f2
    assert bindings.e().roundtrip_flag8(store, Flag8(0)) == Flag8(0)
    for f8 in Flag8:
        assert bindings.e().roundtrip_flag8(store, f8) == f8
    assert bindings.e().roundtrip_flag16(store, Flag16(0)) == Flag16(0)
    for f16 in Flag16:
        assert bindings.e().roundtrip_flag16(store, f16) == f16
    assert bindings.e().roundtrip_flag32(store, Flag32(0)) == Flag32(0)
    for f32 in Flag32:
        assert bindings.e().roundtrip_flag32(store, f32) == f32
    assert bindings.e().roundtrip_flag64(store, Flag64(0)) == Flag64(0)
    for f64 in Flag64:
        assert bindings.e().roundtrip_flag64(store, f64) == f64

    bindings.e().empty_tuple(store, None)

    r = bindings.e().roundtrip_r1(store, R1(8, Flag1(0)))
    assert r.a == 8
    assert r.b == Flag1(0)

    r = bindings.e().roundtrip_r1(store, R1(a=100, b=Flag1.A | Flag1.B))
    assert r.a == 100
    assert r.b == Flag1.A | Flag1.B
