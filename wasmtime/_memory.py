from . import _ffi as ffi
from ctypes import *
import ctypes
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
        error = ffi.wasmtime_memory_new(store._context(), ty.ptr(), byref(mem))
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

        ptr = ffi.wasmtime_memory_type(store._context(), byref(self._memory))
        return MemoryType._from_ptr(ptr, None)

    def grow(self, store: Storelike, delta: int) -> int:
        """
        Grows this memory by the given number of pages
        """

        if delta < 0:
            raise WasmtimeError("cannot grow by negative amount")
        prev = ffi.c_uint64(0)
        error = ffi.wasmtime_memory_grow(store._context(), byref(self._memory), delta, byref(prev))
        if error:
            raise WasmtimeError._from_ptr(error)
        return prev.value

    def size(self, store: Storelike) -> int:
        """
        Returns the size, in WebAssembly pages, of this memory.
        """

        return ffi.wasmtime_memory_size(store._context(), byref(self._memory))

    def data_ptr(self, store: Storelike) -> "ctypes._Pointer[c_ubyte]":
        """
        Returns the raw pointer in memory where this wasm memory lives.

        Remember that all accesses to wasm memory should be bounds-checked
        against the `data_len` method.
        """
        return ffi.wasmtime_memory_data(store._context(), byref(self._memory))

    def get_buffer_ptr(self, store: Storelike,
                       size: typing.Optional[int] = None,
                       offset: int = 0) -> ctypes.Array:
        """
        return raw pointer to buffer suitable for creating zero-copy writable NumPy Buffer Protocol
        this method is also used internally by `read()` and `write()`

        np_mem = np.frombuffer(memory.get_buffer_ptr(store), dtype=np.uint8)
        np_mem[start:end] = A # write
        B = np_mem[start:end] # read
        """
        if size is None:
            size = self.data_len(store)
        ptr_type = ctypes.c_ubyte * size
        return ptr_type.from_address(ctypes.addressof(self.data_ptr(store).contents) + offset)

    def read(
            self,
            store: Storelike,
            start: typing.Optional[int] = 0,
            stop: typing.Optional[int] = None) -> bytearray:
        """
        Reads this memory starting from `start` and up to `stop`
        and returns a copy of the contents as a `bytearray`.

        The indexing behavior of this method is similar to `list[start:stop]`
        where negative starts can be used to read from the end, for example.
        """
        size = self.data_len(store)
        key = slice(start, stop, None)
        start, stop, _ = key.indices(size)
        val_size = stop - start
        if val_size <= 0:
            # return bytearray of size zero
            return bytearray(0)
        src_ptr = self.get_buffer_ptr(store, val_size, start)
        return bytearray(src_ptr)

    def write(
            self,
            store: Storelike,
            value: typing.Union[bytearray, bytes],
            start: typing.Optional[int] = None) -> int:
        """
        write a bytearray value into a possibly large slice of memory
        negative start is allowed in a way similat to list slice mylist[-10:]
        if value is not bytearray it will be used to construct an intermediate bytearray (copyied twice)
        return number of bytes written
        raises IndexError when trying to write outside the memory range
        this happens when start offset is >= size or when end side of value is >= size
        """
        size = self.data_len(store)
        key = slice(start, None)
        start = key.indices(size)[0]
        if start >= size:
            raise IndexError("index out of range")
        # value must be bytearray ex. cast bytes() to bytearray
        if not isinstance(value, bytearray):
            value = bytearray(value)
        val_size = len(value)
        if val_size == 0:
            return val_size
        # stop is exclusive
        stop = start + val_size
        if stop > size:
            raise IndexError("index out of range")
        ptr_type = ctypes.c_ubyte * val_size
        src_ptr = ptr_type.from_buffer(value)
        dst_ptr = self.get_buffer_ptr(store, val_size, start)
        ctypes.memmove(dst_ptr, src_ptr, val_size)
        return val_size

    def data_len(self, store: Storelike) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasmtime_memory_data_size(store._context(), byref(self._memory))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(memory=self._memory)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_MEMORY, union)
