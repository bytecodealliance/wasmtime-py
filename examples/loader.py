# This example shows how you can use the `wasmtime.loader` module to load wasm
# modules as if they were native Python modules

import wasmtime.loader  # noqa: F401

import loader_load_python  # type: ignore
import loader_load_wasm  # type: ignore

# This imports our `loader_add.wat` file next to this module
import loader_add  # type: ignore
assert(loader_add.add(1, 2) == 3)

# This imports our `loader_load_wasm.wat`, which in turn imports
# `loader_load_wasm_target.wat`, which gives us the answer of 4
assert(loader_load_wasm.call_dependency() == 4)

# This imports our `loader_load_python.wat` file which then imports its own
# python file.
assert(loader_load_python.call_python() == 42)
