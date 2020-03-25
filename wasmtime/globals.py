from .ffi import *
from ctypes import *
from wasmtime import Store, GlobalType, Val, Extern

dll.wasm_global_new.restype = P_wasm_global_t
dll.wasm_global_type.restype = P_wasm_globaltype_t
dll.wasm_global_as_extern.restype = P_wasm_extern_t


class Global:
    def __init__(self, store, ty, val):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, GlobalType):
            raise TypeError("expected a GlobalType")
        val = Val.__convert__(ty.content(), val)
        ptr = dll.wasm_global_new(
            store.__ptr__, ty.__ptr__, byref(val.__raw__))
        if not ptr:
            raise RuntimeError("failed to create global")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_global_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Gets the type of this global as a `GlobalType`
    def type(self):
        ptr = dll.wasm_global_type(self.__ptr__)
        return GlobalType.__from_ptr__(ptr, None)

    # Gets the current value of this global
    #
    # Returns a native python type
    def get(self):
        raw = wasm_val_t()
        dll.wasm_global_get(self.__ptr__, byref(raw))
        return Val(raw).get()

    # Sets the value of this global to a new value
    def set(self, val):
        val = Val.__convert__(self.type().content(), val)
        dll.wasm_global_set(self.__ptr__, byref(val.__raw__))

    # Returns this type as an instance of `Extern`
    def as_extern(self):
        ptr = dll.wasm_global_as_extern(self.__ptr__)
        return Extern.__from_ptr__(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_global_delete(self.__ptr__)
