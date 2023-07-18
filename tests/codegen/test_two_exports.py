from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "i" (instance $i
          (export "f1" (func))
          (export "f2" (func))
        ))

        (core func $f1 (canon lower (func $i "f1")))
        (core func $f2 (canon lower (func $i "f2")))

        (func $f1' (canon lift (core func $f1)))
        (func $f2' (canon lift (core func $f2)))

        (instance (export "i1") (export "f1" (func $f1')))
        (instance (export "i2") (export "f2" (func $f2')))
    )
"""
bindgen('two_exports', module)

from .generated.two_exports import Root, RootImports, imports


class Host(imports.I):
    def f1(self) -> None:
        self.f1_hit = True

    def f2(self) -> None:
        self.f2_hit = True


def test_bindings():
    store = Store()
    host = Host()
    wasm = Root(store, RootImports(i=host))

    wasm.i1().f1(store)
    assert(host.f1_hit)
    wasm.i2().f2(store)
    assert(host.f2_hit)
