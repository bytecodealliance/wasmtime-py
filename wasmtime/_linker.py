from ctypes import *
from wasmtime import Instance, Engine, FuncType
from wasmtime import Module, WasmtimeError, Func
from . import _ffi as ffi
from ._extern import get_extern_ptr, wrap_extern
from ._config import setter_property
from ._exportable import AsExtern
from ._store import Storelike
from ._func import enter_wasm, trampoline, FUNCTIONS, finalize
from typing import Callable


class Linker:
    engine: Engine

    def __init__(self, engine: Engine):
        """
        Creates a new linker ready to instantiate modules within the store
        provided.
        """
        self._ptr = ffi.wasmtime_linker_new(engine._ptr)
        self.engine = engine

    @setter_property
    def allow_shadowing(self, allow: bool) -> None:
        """
        Configures whether definitions are allowed to shadow one another within
        this linker
        """
        if not isinstance(allow, bool):
            raise TypeError("expected a boolean")
        ffi.wasmtime_linker_allow_shadowing(self._ptr, allow)

    def define(self, module: str, name: str, item: AsExtern) -> None:
        """
        Defines a new item, by name, in this linker.

        This method will add a new definition to this linker. The `module` nad
        `name` provided are what to name the `item` within the linker.

        This function will raise an error if `item` comes from the wrong store
        or if shadowing is disallowed and the module/name pair has already been
        defined.
        """
        raw_item = get_extern_ptr(item)
        module_bytes = module.encode('utf-8')
        module_buf = create_string_buffer(module_bytes)
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        error = ffi.wasmtime_linker_define(
            self._ptr,
            module_buf,
            len(module_bytes),
            name_buf,
            len(name_bytes),
            byref(raw_item))
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_func(self, module: str, name: str, ty: FuncType, func: Callable, access_caller: bool = False) -> None:
        """
        Defines a new function, by name, in this linker.

        This method is similar to `define` except that you can directly define a
        function without creating a `Func` itself. This enables
        `Store`-independent functions to be inserted into this linker, meaning
        the linker can be used to instantiate modules in multiple stores.
        """
        module_bytes = module.encode('utf-8')
        module_buf = create_string_buffer(module_bytes)
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        if not isinstance(ty, FuncType):
            raise TypeError("expected a FuncType")
        idx = FUNCTIONS.allocate((func, ty.results, access_caller))
        error = ffi.wasmtime_linker_define_func(
            self._ptr,
            module_buf,
            len(module_bytes),
            name_buf,
            len(name_bytes),
            ty._ptr,
            trampoline,
            idx,
            finalize)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_instance(self, store: Storelike, name: str, instance: Instance) -> None:
        """
        Convenience wrapper to define an entire instance in this linker.

        This function will `define` eaech of the exports on the instance into
        this linker, using the name provided as the module name and the export's
        own name as the field name.

        This function will raise an error if `instance` comes from the wrong
        store or if shadowing is disallowed and a name was previously defined.
        """
        if not isinstance(instance, Instance):
            raise TypeError("expected an `Instance`")
        name_bytes = name.encode('utf8')
        name_buf = create_string_buffer(name_bytes)
        error = ffi.wasmtime_linker_define_instance(self._ptr,
                                                    store._context,
                                                    name_buf,
                                                    len(name_bytes),
                                                    byref(instance._instance))
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_wasi(self) -> None:
        """
        Defines a WASI instance in this linker.

        The instance provided has been previously constructed and this method
        will define all the appropriate imports and their names into this linker
        to assist with instantiating modules that use WASI.

        This function will raise an error if shadowing is disallowed and a name
        was previously defined.
        """
        error = ffi.wasmtime_linker_define_wasi(self._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_module(self, store: Storelike, name: str, module: Module) -> None:
        """
        Defines automatic instantiations of the provided module in this linker.

        The `module` provided is defined under `name` with automatic
        instantiations which respect WASI Commands and Reactors.

        For more information see the Rust documentation at
        https://docs.wasmtime.dev/api/wasmtime/struct.Linker.html#method.module.

        This method will throw an error if shadowing is disallowed and an item
        has previously been defined.
        """
        if not isinstance(module, Module):
            raise TypeError("expected a `Module`")
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        error = ffi.wasmtime_linker_module(self._ptr, store._context, name_buf, len(name_bytes), module._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def instantiate(self, store: Storelike, module: Module) -> Instance:
        """
        Instantiates a module using this linker's defined set of names.

        This method will attempt to satisfy all the imports of the `module`
        provided with the names defined within this linker. If all names are
        defined then the module is instantiated.

        Raises an error if an import of `module` hasn't been defined in this
        linker or if a trap happens while instantiating the instance.
        """
        trap = POINTER(ffi.wasm_trap_t)()
        instance = ffi.wasmtime_instance_t()
        with enter_wasm(store) as trap:
            error = ffi.wasmtime_linker_instantiate(
                self._ptr, store._context, module._ptr, byref(instance), trap)
            if error:
                raise WasmtimeError._from_ptr(error)
        return Instance._from_raw(instance)

    def get_default(self, store: Storelike, name: str) -> Func:
        """
        Gets the default export for the named module in this linker.

        For more information on this see the Rust documentation at
        https://docs.wasmtime.dev/api/wasmtime/struct.Linker.html#method.get_default.

        Raises an error if the default export wasn't present.
        """
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        func = ffi.wasmtime_func_t()
        error = ffi.wasmtime_linker_get_default(self._ptr, store._context,
                                                name_buf, len(name_bytes), byref(func))
        if error:
            raise WasmtimeError._from_ptr(error)
        return Func._from_raw(func)

    def get(self, store: Storelike, module: str, name: str) -> AsExtern:
        """
        Gets a singular item defined in this linker.

        Raises an error if this item hasn't been defined or if the item has been
        defined twice with different types.
        """
        module_bytes = module.encode('utf-8')
        module_buf = create_string_buffer(module_bytes)
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        item = ffi.wasmtime_extern_t()
        ok = ffi.wasmtime_linker_get(self._ptr, store._context,
                                     module_buf, len(module_bytes),
                                     name_buf, len(name_bytes),
                                     byref(item))
        if ok:
            return wrap_extern(item)
        raise WasmtimeError("item not defined in linker")

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_linker_delete(self._ptr)
