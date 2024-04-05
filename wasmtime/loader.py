"""
This module is a custom loader for Python which enables importing wasm files
directly into Python programs simply through usage of the `import` statement.

You can import this module with `import wasmtime.loader` and then afterwards you
can `import your_wasm_file` which will automatically compile and instantiate
`your_wasm_file.wasm` and hook it up into Python's module system.
"""

from typing import NoReturn, Iterator, Mapping, Dict
import io
import re
import sys
import struct
from pathlib import Path
from importlib import import_module
from importlib.abc import Loader, MetaPathFinder, ResourceReader
from importlib.machinery import ModuleSpec

from wasmtime import Module, Linker, Store, WasiConfig
from wasmtime import Func, Table, Global, Memory
from wasmtime import wat2wasm, bindgen


predefined_modules = []
store = Store()
linker = Linker(store.engine)
# TODO: how to configure wasi?
store.set_wasi(WasiConfig())
predefined_modules.append("wasi_snapshot_preview1")
predefined_modules.append("wasi_unstable")
linker.define_wasi()
linker.allow_shadowing = True


_component_bindings: Dict[Path, Mapping[str, bytes]] = {}


class _CoreWasmLoader(Loader):
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


class _PythonLoader(Loader):
    def __init__(self, resource_reader: ResourceReader):
        self.resource_reader = resource_reader

    def create_module(self, spec):  # type: ignore
        return None  # use default module creation semantics

    def exec_module(self, module):  # type: ignore
        origin = Path(module.__spec__.origin)
        for component_path, component_files in _component_bindings.items():
            try:
                relative_path = str(origin.relative_to(component_path))
            except ValueError:
                continue
            exec(component_files[relative_path], module.__dict__)
            break

    def get_resource_reader(self, fullname: str) -> ResourceReader:
        return self.resource_reader


class _BindingsResourceReader(ResourceReader):
    def __init__(self, origin: Path):
        self.resources = _component_bindings[origin]

    def contents(self) -> Iterator[str]:
        return iter(self.resources.keys())

    def is_resource(self, path: str) -> bool:
        return path in self.resources

    def open_resource(self, resource: str) -> io.BytesIO:
        if resource not in self.resources:
            raise FileNotFoundError
        return io.BytesIO(self.resources[resource])

    def resource_path(self, resource: str) -> NoReturn:
        raise FileNotFoundError # all of our resources are virtual


class _WasmtimeMetaPathFinder(MetaPathFinder):
    @staticmethod
    def is_component(path: Path, *, binary: bool = True) -> bool:
        if binary:
            with path.open("rb") as f:
                preamble = f.read(8)
            if len(preamble) != 8:
                return False
            magic, version, layer = struct.unpack("<4sHH", preamble)
            if magic != b"\x00asm":
                return False
            if layer != 1: # 0 for core wasm, 1 for components
                return False
            return True
        else:
            contents = path.read_text()
            # Not strictly correct, but should be good enough for most cases where
            # someone is using a component in the textual format.
            return re.search(r"\s*\(\s*component", contents) is not None

    @staticmethod
    def load_component(path: Path, *, binary: bool = True) -> Mapping[str, bytes]:
        component = path.read_bytes()
        if not binary:
            component = wat2wasm(component)
        return bindgen.generate("root", component)

    def find_spec(self, fullname, path, target=None):  # type: ignore
        modname = fullname.split(".")[-1]
        if path is None:
            path = sys.path
        for entry in map(Path, path):
            # Is the requested spec a Python module from generated bindings?
            if entry in _component_bindings:
                # Create a spec with a virtual origin pointing into generated bindings.
                origin = entry / (modname + ".py")
                return ModuleSpec(fullname, _PythonLoader(_BindingsResourceReader(entry)),
                                  origin=origin)
            # Is the requested spec a core Wasm module or a Wasm component?
            for suffix in (".wasm", ".wat"):
                is_binary = (suffix == ".wasm")
                origin = entry / (modname + suffix)
                if origin.exists():
                    # Since the origin is on the filesystem, ensure it has an absolute path.
                    origin = origin.resolve()
                    if self.is_component(origin, binary=is_binary):
                        # Generate bindings for the component and remember them for later.
                        _component_bindings[origin] = self.load_component(origin, binary=is_binary)
                        # Create a spec with a virtual origin pointing into generated bindings,
                        # specifically the `__init__.py` file with the code for the package itself.
                        spec = ModuleSpec(fullname, _PythonLoader(_BindingsResourceReader(origin)),
                                          origin=origin / '__init__.py', is_package=True)
                        # Set the search path to the origin. Importlib will provide both the origin
                        # and the search locations back to this function as-is, even regardless of
                        # types, but try to follow existing Python conventions. The `origin` will
                        # be a key in `_component_bindings`.
                        spec.submodule_search_locations = [origin]
                        return spec
                    else:
                        # Create a spec with a filesystem origin pointing to thg core Wasm module.
                        return ModuleSpec(fullname, _CoreWasmLoader(), origin=origin)
        return None


sys.meta_path.append(_WasmtimeMetaPathFinder())
