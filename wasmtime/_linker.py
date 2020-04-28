from ._ffi import *
from ctypes import *
from wasmtime import Store, Instance
from wasmtime import Module, Trap, WasiInstance, WasmtimeError
from ._extern import get_extern_ptr

dll.wasmtime_linker_new.restype = P_wasmtime_linker_t
dll.wasmtime_linker_define.restype = P_wasmtime_error_t
dll.wasmtime_linker_define_instance.restype = P_wasmtime_error_t
dll.wasmtime_linker_define_wasi.restype = P_wasmtime_error_t
dll.wasmtime_linker_instantiate.restype = P_wasmtime_error_t


def setter_property(fset):
    return property(fset=fset)


class Linker(object):
    def __init__(self, store):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        self.__ptr__ = dll.wasmtime_linker_new(store.__ptr__)
        self.store = store

    @setter_property
    def allow_shadowing(self, allow):
        """
        Configures whether definitions are allowed to shadow one another within
        this linker
        """
        if not isinstance(allow, bool):
            raise TypeError("expected a boolean")
        dll.wasmtime_linker_allow_shadowing(self.__ptr__, allow)

    def define(self, module, name, item):
        raw_item = get_extern_ptr(item)
        module_raw = str_to_name(module)
        name_raw = str_to_name(name)
        error = dll.wasmtime_linker_define(
            self.__ptr__,
            byref(module_raw),
            byref(name_raw),
            raw_item)
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def define_instance(self, name, instance):
        if not isinstance(instance, Instance):
            raise TypeError("expected an `Instance`")
        name_raw = str_to_name(name)
        error = dll.wasmtime_linker_define_instance(self.__ptr__, byref(name_raw),
                                                    instance.__ptr__)
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def define_wasi(self, instance):
        if not isinstance(instance, WasiInstance):
            raise TypeError("expected an `WasiInstance`")
        error = dll.wasmtime_linker_define_wasi(self.__ptr__, instance.__ptr__)
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def instantiate(self, module):
        if not isinstance(module, Module):
            raise TypeError("expected a `Module`")
        trap = P_wasm_trap_t()
        instance = P_wasm_instance_t()
        error = dll.wasmtime_linker_instantiate(
            self.__ptr__, module.__ptr__, byref(instance), byref(trap))
        if error:
            raise WasmtimeError.__from_ptr__(error)
        if trap:
            raise Trap.__from_ptr__(trap)
        return Instance.__from_ptr__(instance, module)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasmtime_linker_delete(self.__ptr__)
