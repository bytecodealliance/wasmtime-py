# The `codegen` directory here is intended to test the bindings generator for
# components in Python. Each file represents a distinct test where an input
# wasm file is bound and then the generated bindings are imported dynamically.
#
# This structure is done so a general `pytest` will execute everything,
# generating bindings during test collection and otherwise setting up everything
# to be naturally checked with mypy and other tests configured.

from wasmtime import wat2wasm
from wasmtime.bindgen import generate
from pathlib import Path
import os

# Helper function to generate bindings for the `wat` specified into the
# `generated` sub-folder. After calling this method the bindings can be
# imported with:
#
#   from .generated.name import Name
#
# and then used to type-check everything.
def bindgen(name: str, wat: str) -> None:
    files = generate(name, wat2wasm(wat))
    root = Path(__file__).parent.joinpath('generated')
    dst = root.joinpath(name)
    for name, contents in files.items():
        # Write the contents to a temporary file and then attempt to atomically
        # replace the previous file, if any, with the new contents. This
        # is done to hopefully fix an apparent issue in `pytest` where it seems
        # that there are multiple threads of the python interpreter, perhaps for
        # pytest itself, mypy, and flake8, and overwriting files in-place causes
        # issues are partial files may be seen.
        file = dst.joinpath(name)
        tmp_file = file.with_suffix('.tmp')
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        tmp_file.write_bytes(contents)
        os.replace(tmp_file, file)
