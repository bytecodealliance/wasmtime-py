from ctypes import *
from wasmtime import Store, Instance
from wasmtime import Module, Trap, WasiInstance, WasmtimeError, Func
from . import _ffi as ffi
from ._extern import get_extern_ptr, wrap_extern
from ._config import setter_property
from ._exportable import AsExtern


class Linker:
    def __init__(self, store: Store):
        """
        Creates a new linker ready to instantiate modules within the store
        provided.
        """
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        self._ptr = ffi.wasmtime_linker_new(store._ptr)
        self.store = store

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
        module_raw = ffi.str_to_name(module)
        name_raw = ffi.str_to_name(name)
        error = ffi.wasmtime_linker_define(
            self._ptr,
            byref(module_raw),
            byref(name_raw),
            raw_item)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_instance(self, name: str, instance: Instance) -> None:
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
        name_raw = ffi.str_to_name(name)
        error = ffi.wasmtime_linker_define_instance(self._ptr, byref(name_raw),
                                                    instance._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_wasi(self, instance: WasiInstance) -> None:
        """
        Defines a WASI instance in this linker.

        The instance provided has been previously constructed and this method
        will define all the appropriate imports and their names into this linker
        to assist with instantiating modules that use WASI.

        This function will raise an error if shadowing is disallowed and a name
        was previously defined.
        """
        if not isinstance(instance, WasiInstance):
            raise TypeError("expected an `WasiInstance`")
        error = ffi.wasmtime_linker_define_wasi(self._ptr, instance._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_module(self, name: str, module: Module) -> None:
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
        name_raw = ffi.str_to_name(name)
        error = ffi.wasmtime_linker_module(self._ptr, byref(name_raw), module._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def instantiate(self, module: Module) -> Instance:
        """
        Instantiates a module using this linker's defined set of names.

        This method will attempt to satisfy all the imports of the `module`
        provided with the names defined within this linker. If all names are
        defined then the module is instantiated.

        Raises an error if an import of `module` hasn't been defined in this
        linker or if a trap happens while instantiating the instance.
        """
        if not isinstance(module, Module):
            raise TypeError("expected a `Module`")
        trap = POINTER(ffi.wasm_trap_t)()
        instance = POINTER(ffi.wasm_instance_t)()
        error = ffi.wasmtime_linker_instantiate(
            self._ptr, module._ptr, byref(instance), byref(trap))
        if error:
            raise WasmtimeError._from_ptr(error)
        if trap:
            raise Trap._from_ptr(trap)
        return Instance._from_ptr(instance, None)

    def get_default(self, name: str) -> Func:
        """
        Gets the default export for the named module in this linker.

        For more information on this see the Rust documentation at
        https://docs.wasmtime.dev/api/wasmtime/struct.Linker.html#method.get_default.

        Raises an error if the default export wasn't present.
        """
        name_raw = ffi.str_to_name(name)
        default = POINTER(ffi.wasm_func_t)()
        error = ffi.wasmtime_linker_get_default(self._ptr, byref(name_raw), byref(default))
        if error:
            raise WasmtimeError._from_ptr(error)
        return Func._from_ptr(default, None)

    def get_one_by_name(self, module: str, name: str) -> AsExtern:
        """
        Gets a singular item defined in this linker.

        Raises an error if this item hasn't been defined or if the item has been
        defined twice with different types.
        """
        module_raw = ffi.str_to_name(module)
        name_raw = ffi.str_to_name(name)
        item = POINTER(ffi.wasm_extern_t)()
        error = ffi.wasmtime_linker_get_one_by_name(self._ptr, byref(module_raw), byref(name_raw), byref(item))
        if error:
            raise WasmtimeError._from_ptr(error)
        return wrap_extern(item, None)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_linker_delete(self._ptr)
