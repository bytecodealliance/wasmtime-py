from .generated import Bindgen, BindgenImports, Err
from typing import Mapping, Tuple
import sys
from wasmtime import Store


class Imports:
    def print(self, list: bytes) -> None:
        sys.stdout.buffer.write(list)

    def eprint(self, list: bytes) -> None:
        sys.stderr.buffer.write(list)


bindgen = None
store = None


def init() -> Tuple[Bindgen, Store]:
    global store
    global bindgen
    if bindgen is None:
        store = Store()
        bindgen = Bindgen(store, BindgenImports(python=Imports()))
    return bindgen, store


# Generates Python bindings for the given component.
#
# The `name` provided is used as the name of the `component` binary provided.
# The `component` argument is expected to be the binary representation of a
# component.
#
# This function returns a mapping of filename to contents of files that are
# generated to represent the Python bindings here.
def generate(name: str, component: bytes) -> Mapping[str, bytes]:
    bindgen, store = init()
    result = bindgen.generate(store, name, component)
    if isinstance(result, Err):
        raise RuntimeError(result.value)
    ret = {}
    for name, contents in result.value:
        ret[name] = contents
    return ret


__all__ = ['generate']
