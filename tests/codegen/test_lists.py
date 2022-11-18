from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "host" (instance $i
        ))
    )
"""
bindgen('lists', module)

from .generated.lists import Lists, ListsImports, imports


class Host(imports.Host):
    pass


def test_bindings():
    store = Store()
    Lists(store, ListsImports(host=Host()))
