from . import _ffi as ffi
from ctypes import *
import ctypes
from wasmtime import MemoryType, WasmtimeError
from ._store import Storelike


class Memory:
    _memory: ffi.wasmtime_memory_t

    def __init__(self, store: Storelike, ty: MemoryType):
        """
        Creates a new memory in `store` with the given `ty`
        """

        mem = ffi.wasmtime_memory_t()
        error = ffi.wasmtime_memory_new(store._context, ty._ptr, byref(mem))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._memory = mem

    @classmethod
    def _from_raw(cls, mem: ffi.wasmtime_memory_t) -> "Memory":
        ty: "Memory" = cls.__new__(cls)
        ty._memory = mem
        return ty

    def type(self, store: Storelike) -> MemoryType:
        """
        Gets the type of this memory as a `MemoryType`
        """

        ptr = ffi.wasmtime_memory_type(store._context, byref(self._memory))
        return MemoryType._from_ptr(ptr, None)

    def grow(self, store: Storelike, delta: int) -> int:
        """
        Grows this memory by the given number of pages
        """

        if delta < 0:
            raise WasmtimeError("cannot grow by negative amount")
        prev = ffi.c_uint64(0)
        error = ffi.wasmtime_memory_grow(store._context, byref(self._memory), delta, byref(prev))
        if error:
            raise WasmtimeError._from_ptr(error)
        return prev.value

    def size(self, store: Storelike) -> int:
        """
        Returns the size, in WebAssembly pages, of this memory.
        """

        return ffi.wasmtime_memory_size(store._context, byref(self._memory))

    def data_ptr(self, store: Storelike) -> "ctypes._Pointer[c_ubyte]":
        """
        Returns the raw pointer in memory where this wasm memory lives.

        Remember that all accesses to wasm memory should be bounds-checked
        against the `data_len` method.
        """
        return ffi.wasmtime_memory_data(store._context, byref(self._memory))

    def data_len(self, store: Storelike) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasmtime_memory_data_size(store._context, byref(self._memory))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(memory=self._memory)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_MEMORY, union)
