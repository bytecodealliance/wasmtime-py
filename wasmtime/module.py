from .ffi import *
from ctypes import *
from wasmtime import Store, wat2wasm

class Module:
    def __init__(self, store, wasm):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        # If this looks like a string, parse it as the text format
        if isinstance(wasm, str):
            wasm = wat2wasm(store.engine, wasm)
        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        binary = wasm_byte_vec_t(len(wasm), cast(wasm, POINTER(c_uint8)))
        ptr = dll.wasm_module_new(store.__ptr__, byref(binary))
        if ptr == 0:
            raise RuntimeError("failed to compile module")
        self.__ptr__ = cast(ptr, P_wasm_module_t)
        self.store = store

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_module_delete(self.__ptr__)
