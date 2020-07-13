from . import _ffi as ffi
from ctypes import *
from wasmtime import TableType, Store, Func, WasmtimeError
from typing import Optional, Any


def get_func_ptr(init: Optional[Func]) -> Optional["pointer[ffi.wasm_func_t]"]:
    if init is None:
        return None
    elif isinstance(init, Func):
        return init._ptr
    else:
        raise TypeError("expected a `Func` or `None`")


class Table:
    _ptr: "pointer[ffi.wasm_table_t]"

    def __init__(self, store: Store, ty: TableType, init: Optional[Func]):
        """
        Creates a new table within `store` with the specified `ty`.

        Note that for now only funcref tables are supported and `init` must
        either be `None` or a `Func`.
        """

        if not isinstance(store, Store):
            raise TypeError("expected a `Store`")
        if not isinstance(ty, TableType):
            raise TypeError("expected a `TableType`")

        init_ptr = get_func_ptr(init)
        ptr = POINTER(ffi.wasm_table_t)()
        error = ffi.wasmtime_funcref_table_new(store._ptr, ty._ptr, init_ptr, byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._ptr = ptr
        self._owner = None

    @classmethod
    def _from_ptr(cls, ptr: "pointer[ffi.wasm_table_t]", owner: Optional[Any]) -> "Table":
        ty: "Table" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_table_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty._owner = owner
        return ty

    @property
    def type(self) -> TableType:
        """
        Gets the type of this table as a `TableType`
        """

        ptr = ffi.wasm_table_type(self._ptr)
        return TableType._from_ptr(ptr, None)

    @property
    def size(self) -> int:
        """
        Gets the size, in elements, of this table
        """

        return ffi.wasm_table_size(self._ptr)

    def grow(self, amt: int, init: Optional[Func]) -> int:
        """
        Grows this table by the specified number of slots, using the specified
        initializer for all new table slots.

        Raises a `WasmtimeError` if the table could not be grown.
        Returns the previous size of the table otherwise.
        """
        init_ptr = get_func_ptr(init)

        prev = c_uint32(0)
        error = ffi.wasmtime_funcref_table_grow(self._ptr, c_uint32(amt), init_ptr, byref(prev))
        if error:
            raise WasmtimeError("failed to grow table")
        return prev.value

    def __getitem__(self, idx: int) -> Optional[Func]:
        """
        Gets an individual element within this table. Currently only works on
        `funcref` tables.

        Returns `None` for a slot where no function has been placed into.
        Returns `Func` for a slot with a function.
        Raises an `WasmtimeError` if `idx` is out of bounds.
        """

        ptr = POINTER(ffi.wasm_func_t)()
        ok = ffi.wasmtime_funcref_table_get(self._ptr, idx, byref(ptr))
        if ok:
            if ptr:
                return Func._from_ptr(ptr, None)
            return None
        raise WasmtimeError("table index out of bounds")

    def __setitem__(self, idx: int, val: Optional[Func]) -> None:
        """
        Sets an individual element within this table. Currently only works on
        `funcref` tables.

        The `val` specified must either be a `Func` or `None`, and `idx` must
        be an integer index.

        Raises a `WasmtimeError` if `idx` is out of bounds.
        """

        val_ptr = get_func_ptr(val)
        error = ffi.wasmtime_funcref_table_set(self._ptr, idx, val_ptr)
        if error:
            raise WasmtimeError._from_ptr(error)

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_table_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_owner') and self._owner is None:
            ffi.wasm_table_delete(self._ptr)
