from . import bindgen, REALLOC
from wasmtime import Store
from typing import List

module = """
    (component
        (import "host" (instance $i
            (export "strings" (func (param "a" string) (result string)))
            (export "bytes" (func (param "a" (list u8)) (result (list u8))))
            (export "ints" (func (param "a" (list u32)) (result (list u32))))
            (export "string-list" (func (param "a" (list string)) (result (list string))))
        ))

        (core module $libc
            (memory (export "mem") 1)
            {}
        )
        (core instance $libc (instantiate $libc))

        (core func $strings (canon lower (func $i "strings")
            (memory $libc "mem") (realloc (func $libc "realloc"))))
        (core func $bytes (canon lower (func $i "bytes")
            (memory $libc "mem") (realloc (func $libc "realloc"))))
        (core func $ints (canon lower (func $i "ints")
            (memory $libc "mem") (realloc (func $libc "realloc"))))
        (core func $string-list (canon lower (func $i "string-list")
            (memory $libc "mem") (realloc (func $libc "realloc"))))

        (core module $m
            (import "libc" "mem" (memory 1))
            (import "" "strings" (func $strings (param i32 i32 i32)))
            (import "" "bytes" (func $bytes (param i32 i32 i32)))
            (import "" "ints" (func $ints (param i32 i32 i32)))
            (import "" "string-list" (func $string-list (param i32 i32 i32)))

            (func (export "strings") (param i32 i32) (result i32)
                (call $strings (local.get 0) (local.get 1) (i32.const 8))
                i32.const 8)
            (func (export "bytes") (param i32 i32) (result i32)
                (call $bytes (local.get 0) (local.get 1) (i32.const 8))
                i32.const 8)
            (func (export "ints") (param i32 i32) (result i32)
                (call $ints (local.get 0) (local.get 1) (i32.const 8))
                i32.const 8)
            (func (export "string-list") (param i32 i32) (result i32)
                (call $string-list (local.get 0) (local.get 1) (i32.const 8))
                i32.const 8)
        )

        (core instance $i (instantiate $m
            (with "libc" (instance $libc))
            (with "" (instance
                (export "strings" (func $strings))
                (export "bytes" (func $bytes))
                (export "ints" (func $ints))
                (export "string-list" (func $string-list))
            ))
        ))

        (func (export "strings") (param "a" string) (result string)
            (canon lift (core func $i "strings")
                (memory $libc "mem") (realloc (func $libc "realloc"))))
        (func (export "bytes") (param "a" (list u8)) (result (list u8))
            (canon lift (core func $i "bytes")
                (memory $libc "mem") (realloc (func $libc "realloc"))))
        (func (export "ints") (param "a" (list u32)) (result (list u32))
            (canon lift (core func $i "ints")
                (memory $libc "mem") (realloc (func $libc "realloc"))))
        (func (export "string-list") (param "a" (list string)) (result (list string))
            (canon lift (core func $i "string-list")
                (memory $libc "mem") (realloc (func $libc "realloc"))))
    )
""".format(REALLOC)
bindgen('lists', module)

from .generated.lists import Root, RootImports, imports


class Host(imports.HostHost):
    def strings(self, a: str) -> str:
        return a

    def bytes(self, a: bytes) -> bytes:
        return a

    def ints(self, a: List[int]) -> List[int]:
        return a

    def string_list(self, a: List[str]) -> List[str]:
        return a


def test_bindings():
    store = Store()
    wasm = Root(store, RootImports(host=Host()))

    assert wasm.strings(store, '') == ''
    assert wasm.strings(store, 'a') == 'a'
    assert wasm.strings(store, 'hello world') == 'hello world'
    assert wasm.strings(store, 'hello ⚑ world') == 'hello ⚑ world'

    assert wasm.bytes(store, b'') == b''
    assert wasm.bytes(store, b'a') == b'a'
    assert wasm.bytes(store, b'\x01\x02') == b'\x01\x02'

    assert wasm.ints(store, []) == []
    assert wasm.ints(store, [1]) == [1]
    assert wasm.ints(store, [1, 2, 100, 10000]) == [1, 2, 100, 10000]

    assert wasm.string_list(store, []) == []
    assert wasm.string_list(store, ['']) == ['']
    assert wasm.string_list(store, ['a', 'b', '', 'd', 'hello']) == ['a', 'b', '', 'd', 'hello']
