from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "host" (instance $host
            (export "thunk" (func))
        ))

        (core module $m
            (import "host" "thunk" (func $thunk))

            (start $thunk)
        )

        (core func $thunk (canon lower (func $host "thunk")))
        (core instance $i (instantiate $m
            (with "host" (instance (export "thunk" (func $thunk))))
        ))
    )
"""
bindgen('simple_import', module)

from .generated.simple_import import Root, RootImports, imports


class Host(imports.Host):
    def thunk(self):
        self.hit = True


def test_bindings():
    store = Store()
    host = Host()
    Root(store, RootImports(host=host))

    assert host.hit
