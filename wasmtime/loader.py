"""
This module is a custom loader for Python which enables importing wasm files
directly into Python programs simply through usage of the `import` statement.

You can import this module with `import wasmtime.loader` and then afterwards you
can `import your_wasm_file` which will automatically compile and instantiate
`your_wasm_file.wasm` and hook it up into Python's module system.
"""

from wasmtime import Module, Linker, Store, WasiConfig
from wasmtime import Func, Table, Global, Memory
import sys
import os.path
import importlib

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location

predefined_modules = []
store = Store()
linker = Linker(store.engine)
# TODO: how to configure wasi?
store.set_wasi(WasiConfig())
predefined_modules.append("wasi_snapshot_preview1")
predefined_modules.append("wasi_unstable")
linker.define_wasi()
linker.allow_shadowing = True

# Mostly copied from
# https://stackoverflow.com/questions/43571737/how-to-implement-an-import-hook-that-can-modify-the-source-code-on-the-fly-using


class _WasmtimeMetaFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):  # type: ignore
        if path is None or path == "":
            path = [os.getcwd()]  # top level import --
            path.extend(sys.path)
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        for entry in path:
            py = os.path.join(str(entry), name + ".py")
            if os.path.exists(py):
                continue
            wasm = os.path.join(str(entry), name + ".wasm")
            if os.path.exists(wasm):
                return spec_from_file_location(fullname, wasm, loader=_WasmtimeLoader(wasm))
            wat = os.path.join(str(entry), name + ".wat")
            if os.path.exists(wat):
                return spec_from_file_location(fullname, wat, loader=_WasmtimeLoader(wat))

        return None


class _WasmtimeLoader(Loader):
    def __init__(self, filename: str):
        self.filename = filename

    def create_module(self, spec):  # type: ignore
        return None  # use default module creation semantics

    def exec_module(self, module):  # type: ignore
        wasm_module = Module.from_file(store.engine, self.filename)

        for wasm_import in wasm_module.imports:
            module_name = wasm_import.module
            # skip modules predefined in library
            if module_name in predefined_modules:
                break
            field_name = wasm_import.name
            imported_module = importlib.import_module(module_name)
            item = imported_module.__dict__[field_name]
            if not isinstance(item, Func) and \
                    not isinstance(item, Table) and \
                    not isinstance(item, Global) and \
                    not isinstance(item, Memory):
                item = Func(store, wasm_import.type, item)
            linker.define(module_name, field_name, item)

        res = linker.instantiate(store, wasm_module)
        exports = res.exports(store)
        for i, export in enumerate(wasm_module.exports):
            item = exports[i]
            # Calling a function requires a `Store`, so bind the first argument
            # to our loader's store
            if isinstance(item, Func):
                func = item
                item = lambda *args,func=func: func(store, *args)  # noqa
            module.__dict__[export.name] = item


sys.meta_path.insert(0, _WasmtimeMetaFinder())
