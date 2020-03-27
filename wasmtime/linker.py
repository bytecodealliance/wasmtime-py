from .ffi import *
from ctypes import *
from wasmtime import Store, Extern, Func, Global, Table, Memory, Instance, Module, Trap

dll.wasmtime_linker_new.restype = P_wasmtime_linker_t
dll.wasmtime_linker_define.restype = c_bool
dll.wasmtime_linker_define_instance.restype = c_bool
dll.wasmtime_linker_instantiate.restype = P_wasm_instance_t


class Linker(object):
    def __init__(self, store):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        self.__ptr__ = dll.wasmtime_linker_new(store.__ptr__)
        self.store = store

    def allow_shadowing(self, allow):
        if not isinstance(allow, bool):
            raise TypeError("expected a boolean")
        dll.wasmtime_linker_allow_shadowing(self.__ptr__, allow)

    def define(self, module, name, item):
        if isinstance(item, Extern):
            raw_item = item.__ptr__
        elif isinstance(item, Func):
            raw_item = item.as_extern().__ptr__
        elif isinstance(item, Global):
            raw_item = item.as_extern().__ptr__
        elif isinstance(item, Memory):
            raw_item = item.as_extern().__ptr__
        elif isinstance(item, Table):
            raw_item = item.as_extern().__ptr__
        else:
            raise TypeError("expected an `Extern`")
        module_raw = str_to_name(module)
        name_raw = str_to_name(name)
        ok = dll.wasmtime_linker_define(self.__ptr__, byref(module_raw),
                byref(name_raw), raw_item)
        if not ok:
            raise RuntimeError("failed to define item")

    def define_instance(self, name, instance):
        if not isinstance(instance, Instance):
            raise TypeError("expected an `Instance`")
        name_raw = str_to_name(name)
        ok = dll.wasmtime_linker_define_instance(self.__ptr__, byref(name_raw),
                instance.__ptr__)
        if not ok:
            raise RuntimeError("failed to define item")

    def instantiate(self, module):
        if not isinstance(module, Module):
            raise TypeError("expected a `Module`")
        trap = P_wasm_trap_t()
        ptr = dll.wasmtime_linker_instantiate(self.__ptr__, module.__ptr__, byref(trap))
        if not ptr:
            if trap:
                trap = Trap.__from_ptr__(trap)
                raise RuntimeError("failed to instantiate: " + trap.message())
            raise RuntimeError("failed to instantiate")
        return Instance.__from_ptr__(ptr)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasmtime_linker_delete(self.__ptr__)

