from . import bindgen
from wasmtime import Store

module = """
    (component)
"""
bindgen('empty', module)

from .generated.empty import Empty


def test_bindings(tmp_path):
    Empty(Store())
