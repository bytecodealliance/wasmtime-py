from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "false" (instance $i
            (type $c1 (variant (case "break" s32) (case "class" s64) (case "true" s64)))
            (export "none" (type $c1' (eq $c1)))
            (export "as" (func (param "import" $c1') (result s64)))

            (type $r1 (record (field "else" u8) (field "not" u8) (field "except" u8)))
            (export "true" (type $r1' (eq $r1)))
            (export "lambda" (func (param "def" $r1') (result u32)))
        ))

        (core func $as (canon lower (func $i "as")))
        (core func $lambda (canon lower (func $i "lambda")))

        (core module $m
            (import "" "as" (func $as (param i32 i64) (result i64)))
            (import "" "lambda" (func $lambda (param i32 i32 i32) (result i32)))

            (func (export "await") (result i32)
                i32.const 100)

            (func (export "as") (param i32 i64) (result i64)
                (call $as (local.get 0) (local.get 1)))

            (func (export "lambda") (param i32 i32 i32) (result i32)
                (call $lambda (local.get 0) (local.get 1) (local.get 2)))
        )

        (core instance $i (instantiate $m
            (with "" (instance
                (export "as" (func $as))
                (export "lambda" (func $lambda))
            ))
        ))

        (type $c1 (variant (case "break" s32) (case "class" s64) (case "true" s64)))
        (type $r1 (record (field "else" u8) (field "not" u8) (field "except" u8)))

        (func $await-export (result u8) (canon lift (core func $i "await")))
        (func $as-export (param "import" $c1) (result s64)
            (canon lift (core func $i "as")))
        (func $lambda-export (param "def" $r1) (result u32)
            (canon lift (core func $i "lambda")))

        (instance (export "for")
            (export "none" (type $c1))
            (export "true" (type $r1))
            (export "await" (func $await-export))
            (export "as" (func $as-export))
            (export "lambda" (func $lambda-export))
        )
    )
"""
bindgen('keywords', module)

from .generated.keywords import Root, RootImports, imports
from .generated.keywords import for_
from .generated.keywords.imports import false


class Host(imports.HostFalse):
    def as_(self, import_):
        if isinstance(import_, false.None_Break):
            return import_.value + 1
        if isinstance(import_, false.None_Class):
            return import_.value + 2
        if isinstance(import_, false.None_True_):
            return import_.value + 3
        else:
            raise ValueError("Invalid input value!")

    def lambda_(self, def_):
        return def_.else_ + def_.not_ + def_.except_


def test_bindings():
    store = Store()
    bindings = Root(store, RootImports(false=Host()))
    assert 100 == bindings.for_().await_(store)
    assert 101 == bindings.for_().as_(store, for_.None_Break(100))
    assert 102 == bindings.for_().as_(store, for_.None_Class(100))
    assert 103 == bindings.for_().as_(store, for_.None_True_(100))
    assert 24 == bindings.for_().lambda_(store, for_.True_(7, 8, 9))
