from . import _ffi as ffi
from ctypes import *
from wasmtime import Store, MemoryType, WasmtimeError
from typing import Optional, Any


class Memory:
    def __init__(self, store: Store, ty: MemoryType):
        """
        Creates a new memory in `store` with the given `ty`
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, MemoryType):
            raise TypeError("expected a MemoryType")
        ptr = ffi.wasm_memory_new(store._ptr, ty._ptr)
        if not ptr:
            raise WasmtimeError("failed to create memory")
        self._ptr = ptr
        self._owner = None

    @classmethod
    def __from_ptr__(cls, ptr: "pointer[ffi.wasm_memory_t]", owner: Optional[Any]) -> "Memory":
        ty: "Memory" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_memory_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty._owner = owner
        return ty

    @property
    def type(self) -> MemoryType:
        """
        Gets the type of this memory as a `MemoryType`
        """

        ptr = ffi.wasm_memory_type(self._ptr)
        return MemoryType.__from_ptr__(ptr, None)

    def grow(self, delta: int) -> bool:
        """
        Grows this memory by the given number of pages
        """

        if not isinstance(delta, int):
            raise TypeError("expected an integer")
        if delta < 0:
            raise WasmtimeError("cannot grow by negative amount")
        ok = ffi.wasm_memory_grow(self._ptr, delta)
        if ok:
            return True
        else:
            return False

    @property
    def size(self) -> int:
        """
        Returns the size, in WebAssembly pages, of this memory.
        """

        return ffi.wasm_memory_size(self._ptr)

    @property
    def data_ptr(self) -> "pointer[c_ubyte]":
        """
        Returns the raw pointer in memory where this wasm memory lives.

        Remember that all accesses to wasm memory should be bounds-checked
        against the `data_len` method.
        """
        return ffi.wasm_memory_data(self._ptr)

    @property
    def data_len(self) -> int:
        """
        Returns the raw byte length of this memory.
        """

        return ffi.wasm_memory_data_size(self._ptr)

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_memory_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_owner') and self._owner is None:
            ffi.wasm_memory_delete(self._ptr)
