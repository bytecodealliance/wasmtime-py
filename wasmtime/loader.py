"""
This module is a custom loader for Python which enables importing wasm files
directly into Python programs simply through usage of the `import` statement.

You can import this module with `import wasmtime.loader` and then afterwards you
can `import your_wasm_file` which will automatically compile and instantiate
`your_wasm_file.wasm` and hook it up into Python's module system.
"""

import sys
from pathlib import Path
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location

from wasmtime import Module, Linker, Store, WasiConfig
from wasmtime import Func, Table, Global, Memory


predefined_modules = []
store = Store()
linker = Linker(store.engine)
# TODO: how to configure wasi?
store.set_wasi(WasiConfig())
predefined_modules.append("wasi_snapshot_preview1")
predefined_modules.append("wasi_unstable")
linker.define_wasi()
linker.allow_shadowing = True


class _WasmtimeLoader(Loader):
    def create_module(self, spec):  # type: ignore
        return None  # use default module creation semantics

    def exec_module(self, module):  # type: ignore
        wasm_module = Module.from_file(store.engine, module.__spec__.origin)

        for wasm_import in wasm_module.imports:
            module_name = wasm_import.module
            if module_name in predefined_modules:
                break
            field_name = wasm_import.name
            imported_module = import_module(module_name)
            item = imported_module.__dict__[field_name]
            if not isinstance(item, (Func, Table, Global, Memory)):
                item = Func(store, wasm_import.type, item)
            linker.define(store, module_name, field_name, item)

        exports = linker.instantiate(store, wasm_module).exports(store)
        for index, wasm_export in enumerate(wasm_module.exports):
            item = exports.by_index[index]
            if isinstance(item, Func):
                # Partially apply `item` to `store`.
                item = (lambda func: lambda *args: func(store, *args))(item)
            module.__dict__[wasm_export.name] = item


class _WasmtimeMetaPathFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):  # type: ignore
        modname = fullname.split(".")[-1]
        if path is None:
            path = sys.path
        for entry in map(Path, path):
            for suffix in (".wasm", ".wat"):
                pathname = entry / (modname + suffix)
                if pathname.exists():
                    return spec_from_file_location(fullname, pathname, loader=_WasmtimeLoader())
        return None


sys.meta_path.append(_WasmtimeMetaPathFinder())
