from . import bindgen, REALLOC
from wasmtime import Store

module = """
(component $OuterComp

   (type $types
        (instance
            (type $runtime-value (variant
                (case "id" string) (case "id2" string)))
            (export $runtime-value-export "runtime-value"
                (type (eq $runtime-value)))
        )
    )
    (import "types" (instance $types (type $types)))
    (alias export $types "runtime-value" (type $runtime-value-export))

    (import "host" (instance $inst
        (alias outer $OuterComp 1 (type $runtime-value))
        (export $export "runtime-value" (type (eq $runtime-value)))
        (export "some-fn" (func (param "v" $export) (result $export)))
    ))

    (core module $libc
        (memory (export "mem") 1)
        {}
    )
    (core instance $libc (instantiate $libc))

    (core module $mod
        (import "libc" "mem" (memory 1))
        (import "" "lowered-fn-import"
            (func $lowered-fn (param i32 i32 i32 i32)))

        (func (export "core-fn") (param i32 i32 i32) (result i32)
            (call $lowered-fn
                (local.get 0) (local.get 1) (local.get 2) (local.get 2))
            (local.get 2))
    )

    (core func $lowered-fn
        (canon lower (func $inst "some-fn") (memory $libc "mem")
            (realloc (func $libc "realloc"))))

    (core instance $inst
        (instantiate $mod
            (with "libc" (instance $libc))
            (with "" (instance
                (export "lowered-fn-import" (func $lowered-fn))
             ))
        )
    )

    (type $runtime-value (variant (case "id" string) (case "id2" string)))
    (func $lifted-core-fn (param "a" $runtime-value) (result $runtime-value)
        (canon lift (core func $inst "core-fn") (memory $libc "mem")
            (realloc (func $libc "realloc"))))

    (instance (export "e")
        (export "runtime-value" (type $runtime-value))
        (export "some-fn" (func $lifted-core-fn))
    )

)
""".format(REALLOC)
bindgen('external_types', module)

from .generated.external_types import Root, RootImports, imports
from .generated.external_types.imports import host
from .generated.external_types import e


class Host(imports.HostHost):
    def some_fn(self, v: host.RuntimeValue) -> host.RuntimeValue:
        return v


def test_bindings(tmp_path):
    store = Store()
    wasm = Root(store, RootImports(None, host=Host()))

    exports = wasm.e()
    rt_id = exports.some_fn(store, e.RuntimeValueId('1234'))
    assert rt_id == e.RuntimeValueId('1234')
