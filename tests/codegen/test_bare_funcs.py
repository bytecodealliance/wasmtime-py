from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "foo-import" (func $foo-import (param "a" s32) (result s32)))

        (core func $foo-import-lowered (canon lower (func $foo-import)))

        (core module $m
            (import "" "foo" (func $foo (param i32) (result i32)))

            (func (export "foo") (param i32) (result i32)
                (call $foo (local.get 0))
            )
        )

        (core instance $i (instantiate $m
            (with "" (instance
                (export "foo" (func $foo-import-lowered))
            ))
        ))

        (func $foo-export-lifted (param "a" s32) (result s32) (canon lift (core func $i "foo")))

        (export "foo-export" (func $foo-export-lifted))
    )
"""
bindgen('bare_funcs', module)

from .generated.bare_funcs import Root, RootImports, imports


class Host(imports.Host):
    def foo_import(self, a):
        return a + 1


def test_bindings():
    store = Store()
    bindings = Root(store, RootImports(host=Host()))
    assert 101 == bindings.foo_export(store, 100)
