# The `codegen` directory here is intended to test the bindings generator for
# components in Python. Each file represents a distinct test where an input
# wasm file is bound and then the generated bindings are imported dynamically.
#
# This structure is done so a general `pytest` will execute everything,
# generating bindings during test collection and otherwise setting up everything
# to be naturally checked with mypy and other tests configured.

from wasmtime.bindgen import generate
from pathlib import Path


# Helper function to generate bindings for the `wat` specified into the
# `generated` sub-folder. After calling this method the bindings can be
# imported with:
#
#   from .generated.name import Name
#
# and then used to type-check everything.
def bindgen(name: str, wat: str) -> None:
    files = generate(name, wat.encode())
    dst = Path(__file__).parent.joinpath('generated').joinpath(name)
    for name, contents in files.items():
        file = dst.joinpath(name)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        file.write_bytes(contents)
