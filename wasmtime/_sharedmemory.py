from . import _ffi as ffi
from ctypes import *
import ctypes
import typing
from wasmtime import MemoryType, WasmtimeError, Engine
from ._store import Storelike



class SharedMemory:
    _sharedmemory: ffi.wasmtime_sharedmemory_t

    def __init__(self, engine: Engine, ty: MemoryType):
        """
        Creates a new shared memory in `store` with the given `ty`
        """

        sharedmemory = ffi.wasmtime_sharedmemory_t()
        ptr = POINTER(ffi.wasmtime_sharedmemory_t)()
        error = ffi.wasmtime_sharedmemory_new(engine.ptr(), ty.ptr(), byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._sharedmemory = sharedmemory

    @classmethod
    def _from_raw(cls, sharedmemory: ffi.wasmtime_sharedmemory_t) -> "SharedMemory":
        ty: "SharedMemory" = cls.__new__(cls)
        ty._sharedmemory = sharedmemory
        return ty

    def type(self) -> MemoryType:
        """
        Gets the type of this memory as a `MemoryType`
        """

        ptr = ffi.wasmtime_sharedmemory_type(byref(self._sharedmemory))
        return MemoryType._from_ptr(ptr, None)

    def grow(self, delta: int) -> int:
        """
        Grows this memory by the given number of pages
        """

        if delta < 0:
            raise WasmtimeError("cannot grow by negative amount")
        prev = ffi.c_uint64(0)
        error = ffi.wasmtime_sharedmemory_grow(byref(self._sharedmemory), delta, byref(prev))
        if error:
            raise WasmtimeError._from_ptr(error)
        return prev.value

    def size(self) -> int:
        """
        Returns the size, in WebAssembly pages, of this shared memory.
        """

        return ffi.wasmtime_sharedmemory_size(byref(self._sharedmemory))

    def data_ptr(self) -> "ctypes._Pointer[c_ubyte]":
        """
        Returns the raw pointer in memory where this wasm shared memory lives.

        Remember that all accesses to wasm shared memory should be bounds-checked
        against the `data_len` method.
        """
        return ffi.wasmtime_sharedmemory_data(byref(self._sharedmemory))

    def data_len(self) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasmtime_sharedmemory_data_size(byref(self._sharedmemory))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(sharedmemory=pointer(self._sharedmemory))
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_SHAREDMEMORY, union)
