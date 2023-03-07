from . import _ffi as ffi
from ctypes import *
import ctypes
import array
import typing
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

    def read(
            self,
            store: Storelike,
            start: typing.Optional[int] = 0,
            stop: typing.Optional[int] = None,
            step: typing.Optional[int] = None) -> typing.Any:
        """
        provide fast way to read large memory slice similar to list[start:stop:step]
        negative start, stop is allowed in a way similat to list slice mylist[-10:]
        """
        data_ptr = self.data_ptr(store)
        size = self.data_len(store)
        key = slice(start, stop, step)
        start, stop, step = key.indices(size)
        val_size = stop - start
        if val_size <= 0:
            # return bytearray of size zero
            return bytearray(0)
        ptr_type = ctypes.c_ubyte * val_size
        src_ptr = (ptr_type).from_address(ctypes.addressof(data_ptr.contents) + start)
        value = bytearray(src_ptr)
        if step != 1:
            value[::step]
        return value

    def write(
            self,
            store: Storelike,
            value: typing.Any,
            start: typing.Optional[int] = 0,
            stop: typing.Optional[int] = None) -> typing.Any:
        """
        write into a possibly large slice of memory
        negative start, stop is allowed in a way similat to list slice mylist[-10:]
        """
        data_ptr = self.data_ptr(store)
        size = self.data_len(store)
        key = slice(start, stop)
        start, stop, step = key.indices(size)
        # value must be bytearray ex. cast bytes() to bytearray
        if not isinstance(value, array.array) and not isinstance(value, bytearray):
            # value = array.array('B', value)
            value = bytearray(value)
        val_size = len(value)
        # key.indices(size) knows about size but not val_size
        stop = start + min(stop - start, val_size)
        # NOTE: we can use * 1, because we need pointer to the start only
        ptr_type = ctypes.c_ubyte * val_size
        src_ptr = (ptr_type).from_buffer(value)
        dst_ptr = ctypes.addressof(
            (ptr_type).from_address(ctypes.addressof(data_ptr.contents) + start)
        )
        ctypes.memmove(dst_ptr, src_ptr, val_size)
        return value

    def data_len(self, store: Storelike) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasmtime_memory_data_size(store._context, byref(self._memory))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(memory=self._memory)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_MEMORY, union)
