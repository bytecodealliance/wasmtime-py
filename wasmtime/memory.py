from .ffi import *
from ctypes import *
from wasmtime import Store, MemoryType

dll.wasm_memory_data.restype = POINTER(c_uint8)
dll.wasm_memory_data_size.restype = c_size_t
dll.wasm_memory_new.restype = P_wasm_memory_t
dll.wasm_memory_type.restype = P_wasm_memorytype_t

class Memory:
    # Creates a new memory in `store` with the given `ty`
    def __init__(self, store, ty):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, MemoryType):
            raise TypeError("expected a MemoryType")
        ptr = dll.wasm_memory_new(store.__ptr__, ty.__ptr__)
        if not ptr:
            raise RuntimeError("failed to create memory")
        self.__ptr__ = ptr
        self.store = store

    # Gets the type of this memory as a `MemoryType`
    def type(self):
        ptr = dll.wasm_memory_type(self.__ptr__)
        return MemoryType.__from_ptr__(ptr, None)

    # Grows this memory by the given number of pages
    def grow(self, delta):
        if not isinstance(delta, int):
            raise TypeError("expected an integer")
        if delta < 0:
            raise RuntimeError("cannot grow by negative amount")
        ok = dll.wasm_memory_grow(self.__ptr__, delta)
        if ok:
            return True
        else:
            return False

    # Returns the size, in WebAssembly pages, of this memory.
    def size(self):
        return dll.wasm_memory_size(self.__ptr__)

    # Returns the raw pointer in memory where this wasm memory lives.
    def data_ptr(self):
        return dll.wasm_memory_data(self.__ptr__)

    # Returns the raw byte length of this memory.
    def data_len(self):
        return dll.wasm_memory_data_size(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_memory_delete(self.__ptr__)

