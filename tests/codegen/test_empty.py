from . import bindgen
from wasmtime import Store

module = """
    (component)
"""
bindgen('empty', module)

from .generated.empty import Root


def test_bindings(tmp_path):
    Root(Store())
