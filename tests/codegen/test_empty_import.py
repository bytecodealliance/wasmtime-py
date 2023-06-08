from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "host" (instance))
    )
"""
bindgen('empty_import', module)

from .generated.empty_import import Root
from .generated.empty_import.imports import RootImports


def test_bindings(tmp_path) -> None:
    Root(Store(), RootImports(host={}))
