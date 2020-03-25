from .ffi import *
from ctypes import *
from wasmtime import Store, GlobalType, Val

dll.wasm_global_new.restype = P_wasm_global_t
dll.wasm_global_type.restype = P_wasm_globaltype_t

class Global:
    def __init__(self, store, ty, val):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, GlobalType):
            raise TypeError("expected a GlobalType")
        if not isinstance(val, Val):
            raise TypeError("expected a Val")
        ptr = dll.wasm_global_new(store.__ptr__, ty.__ptr__, byref(val.__raw__))
        if not ptr:
            raise RuntimeError("failed to create global")
        self.__ptr__ = ptr
        self.store = store

    # Gets the type of this global as a `GlobalType`
    def type(self):
        ptr = dll.wasm_global_type(self.__ptr__)
        return GlobalType.__from_ptr__(ptr, None)

    # Gets the current value of this global
    def get(self):
        raw = wasm_val_t()
        dll.wasm_global_get(self.__ptr__, byref(raw))
        return Val(raw)

    # Sets the value of this global to a new value
    def set(self, val):
        if not isinstance(val, Val):
            raise TypeError("expected a Val")
        dll.wasm_global_set(self.__ptr__, byref(val.__raw__))

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_global_delete(self.__ptr__)
