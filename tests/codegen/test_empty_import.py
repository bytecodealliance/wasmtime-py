from . import bindgen
from wasmtime import Store

module = """
    (component
        (import "host" (instance))
    )
"""
bindgen('empty_import', module)

from .generated.empty_import import EmptyImport, EmptyImportImports


def test_bindings(tmp_path):
    EmptyImport(Store(), EmptyImportImports(host={}))
