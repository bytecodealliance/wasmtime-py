from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "host" (instance $i
            (export "many-arguments" (func
                (param "a1" u64)
                (param "a2" u64)
                (param "a3" u64)
                (param "a4" u64)
                (param "a5" u64)
                (param "a6" u64)
                (param "a7" u64)
                (param "a8" u64)
                (param "a9" u64)
                (param "a10" u64)
                (param "a11" u64)
                (param "a12" u64)
                (param "a13" u64)
                (param "a14" u64)
                (param "a15" u64)
                (param "a16" u64)
            ))
        ))
        (core module $m
            (import "" "" (func $f (param
                i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64
            )))

            (func (export "")
                (param
                    i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64 i64
                )
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
                local.get 12
                local.get 13
                local.get 14
                local.get 15
                call $f
            )
        )
        (core func $f (canon lower (func $i "many-arguments")))

        (core instance $i (instantiate $m
            (with "" (instance (export "" (func $f))))
        ))

        (func (export "many-arguments")
                (param "a1" u64)
                (param "a2" u64)
                (param "a3" u64)
                (param "a4" u64)
                (param "a5" u64)
                (param "a6" u64)
                (param "a7" u64)
                (param "a8" u64)
                (param "a9" u64)
                (param "a10" u64)
                (param "a11" u64)
                (param "a12" u64)
                (param "a13" u64)
                (param "a14" u64)
                (param "a15" u64)
                (param "a16" u64)
            (canon lift (core func $i "")))
    )
"""
bindgen('many_arguments', module)

from .generated.many_arguments import ManyArguments, ManyArgumentsImports, imports


class MyImports(imports.Host):
    def many_arguments(self,
                       a1: int,
                       a2: int,
                       a3: int,
                       a4: int,
                       a5: int,
                       a6: int,
                       a7: int,
                       a8: int,
                       a9: int,
                       a10: int,
                       a11: int,
                       a12: int,
                       a13: int,
                       a14: int,
                       a15: int,
                       a16: int) -> None:
        assert(a1 == 1)
        assert(a2 == 2)
        assert(a3 == 3)
        assert(a4 == 4)
        assert(a5 == 5)
        assert(a6 == 6)
        assert(a7 == 7)
        assert(a8 == 8)
        assert(a9 == 9)
        assert(a10 == 10)
        assert(a11 == 11)
        assert(a12 == 12)
        assert(a13 == 13)
        assert(a14 == 14)
        assert(a15 == 15)
        assert(a16 == 16)


def test_bindings():
    store = Store()
    wasm = ManyArguments(store, ManyArgumentsImports(MyImports()))
    wasm.many_arguments(store, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
