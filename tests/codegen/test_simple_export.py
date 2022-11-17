from . import bindgen
from wasmtime import Store

module = """
    (component
        (core module $m
            (func (export "get") (result i32)
                i32.const 100)
        )

        (core instance $i (instantiate $m))

        (func (export "get") (result u8) (canon lift (core func $i "get")))
    )
"""
bindgen('simple_export', module)

from .generated.simple_export import SimpleExport

def test_bindings():
    store = Store()
    bindings = SimpleExport(store)
    result = bindings.get(store)
    assert result == 100

