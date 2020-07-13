from ctypes import *
from wasmtime import Store, Instance
from wasmtime import Module, Trap, WasiInstance, WasmtimeError
from . import _ffi as ffi
from ._extern import get_extern_ptr
from ._config import setter_property
from ._exportable import AsExtern


class Linker:
    def __init__(self, store: Store):
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
        if not isinstance(instance, Instance):
            raise TypeError("expected an `Instance`")
        name_raw = ffi.str_to_name(name)
        error = ffi.wasmtime_linker_define_instance(self._ptr, byref(name_raw),
                                                    instance._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def define_wasi(self, instance: WasiInstance) -> None:
        if not isinstance(instance, WasiInstance):
            raise TypeError("expected an `WasiInstance`")
        error = ffi.wasmtime_linker_define_wasi(self._ptr, instance._ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def instantiate(self, module: Module) -> Instance:
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
        return Instance._from_ptr(instance, module)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_linker_delete(self._ptr)
