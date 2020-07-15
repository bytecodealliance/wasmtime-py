from . import _ffi as ffi
from ctypes import *
from wasmtime import TableType, Store, WasmtimeError, IntoVal, Val, ValType
from typing import Optional, Any


class Table:
    _ptr: "pointer[ffi.wasm_table_t]"

    def __init__(self, store: Store, ty: TableType, init: IntoVal):
        """
        Creates a new table within `store` with the specified `ty`.
        """

        if not isinstance(store, Store):
            raise TypeError("expected a `Store`")
        if not isinstance(ty, TableType):
            raise TypeError("expected a `TableType`")

        init_val = Val._convert(ty.element, init)

        ptr = ffi.wasm_table_new(store._ptr, ty._ptr, init_val._unwrap_raw().of.ref)
        if not ptr:
            raise WasmtimeError("Failed to create table")
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

    def grow(self, amt: int, init: IntoVal) -> int:
        """
        Grows this table by the specified number of slots, using the specified
        initializer for all new table slots.

        Raises a `WasmtimeError` if the table could not be grown.
        Returns the previous size of the table otherwise.
        """
        init_val = Val._convert(self.type.element, init)
        ok = ffi.wasm_table_grow(self._ptr, c_uint32(amt), init_val._unwrap_raw().of.ref)
        if not ok:
            raise WasmtimeError("failed to grow table")
        return self.size - amt

    def __getitem__(self, idx: int) -> Optional[Any]:
        """
        Gets an individual element within this table.

        Returns `None` for null references in the table (i.e. a null `funcref`
        or a null `externref).

        Returns a `Func` for non-null `funcref` table elements.

        Returns the wrapped extern data for non-null `externref` table elements.

        Raises an `WasmtimeError` if `idx` is out of bounds.
        """
        if idx >= self.size:
            raise WasmtimeError("table index out of bounds")

        if self.type.element == ValType.externref():
            val = Val.externref(None)
        elif self.type.element == ValType.funcref():
            val = Val.funcref(None)
        else:
            raise WasmtimeError("unsupported table element type")

        val._unwrap_raw().of.ref = ffi.wasm_table_get(self._ptr, idx)
        return val.value

    def __setitem__(self, idx: int, val: IntoVal) -> None:
        """
        Sets an individual element within this table.

        `idx` must be an integer index.

        The `val` specified must be convertible into this table's element
        type. I.e. for a `funcref` table, `val` must either be a `Func` or
        `None`, and for an `externref` table, `val` may be any arbitrary
        external data.

        Raises a `WasmtimeError` if `idx` is out of bounds.
        """
        if idx >= self.size:
            raise WasmtimeError("Index out of bounds when setting table element")

        value = Val._convert(self.type.element, val)
        ok = ffi.wasm_table_set(self._ptr, idx, value._unwrap_raw().of.ref)
        if not ok:
            raise WasmtimeError("Failed to set table element")

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_table_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_owner') and self._owner is None:
            ffi.wasm_table_delete(self._ptr)
