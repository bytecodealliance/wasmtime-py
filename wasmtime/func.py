from .ffi import *
from ctypes import *
from wasmtime import Store, FuncType

dll.wasm_func_new.restype = P_wasm_func_t
dll.wasm_func_type.restype = P_wasm_functype_t

@CFUNCTYPE(P_wasm_trap_t, c_void_p, POINTER(wasm_val_t), POINTER(wasm_val_t))
def trampoline(params, results):
    pass

class Func:
    # Creates a new func in `store` with the given `ty` which calls the closure
    # given
    def __init__(self, store, ty, func):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, FuncType):
            raise TypeError("expected a FuncType")
        ptr = dll.wasm_func_new(store.__ptr__, ty.__ptr__)
        if not ptr:
            raise RuntimeError("failed to create func")
        self.__ptr__ = ptr
        self.store = store

    # Gets the type of this func as a `FuncType`
    def type(self):
        ptr = dll.wasm_func_type(self.__ptr__)
        return FuncType.__from_ptr__(ptr, None)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_func_delete(self.__ptr__)

