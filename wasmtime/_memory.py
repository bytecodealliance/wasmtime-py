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

    def set_store(self, store: Storelike):
        """
        must be called to set the store for highlevel access of memory
        """
        self._store=store

    def __getitem__(self, key: int):
        """
        provide memory[offset] or memory[start:stop]
        """
        if self._store is None:
            raise RuntimeError("you must call `set_store()` before using highlevel access")
        data_ptr = self.data_ptr(self._store)
        size = self.data_len(self._store)
        if isinstance(key, int):
            if key>=size:
                raise IndexError("out of memory size")
            return data_ptr[key]
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")
        start = key.start
        stop = key.stop
        if key.step is not None:
            raise ValueError("slice with step is not supported")

        val_size = stop - start
        value = bytearray(val_size)

        if stop is None:
            stop = start+val_size
        if stop>size:
            raise IndexError("out of memory size")
        dst_ptr = (ctypes.c_ubyte * val_size).from_buffer(value)
        src_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)
        return value

    def __setitem__(self, key, value: bytearray):
        """
        provide setter for memory[key] with slice support

        memory[offset]=value
        memory[start:stop]=b'hello world'
        memory[start:stop]=bytearray([1,2,3])
        """
        if self._store is None:
            raise RuntimeError("you must call `set_store()` before using highlevel access")
        data_ptr = self.data_ptr(self._store)
        size = self.data_len(self._store)
        if isinstance(key, int):
            if key>=size:
                raise IndexError("out of memory size")
            data_ptr[key] = value
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")
        start = key.start
        stop = key.stop
        if key.step is not None:
            raise ValueError("slice with step is not supported")
        val_size = len(value)
        if stop is None:
            stop=start+val_size
        if stop-start>val_size or stop>size:
            raise IndexError("out of memory size")
        src_ptr = (ctypes.c_ubyte * val_size).from_buffer(value)
        dst_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)

    def data_len(self, store: Storelike) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasmtime_memory_data_size(store._context, byref(self._memory))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(memory=self._memory)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_MEMORY, union)
