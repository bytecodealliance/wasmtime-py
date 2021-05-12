from . import _ffi as ffi
from ctypes import *
from wasmtime import TableType, Store, WasmtimeError, IntoVal, Val
from typing import Optional, Any
from ._store import Storelike


class Table:
    _table: ffi.wasmtime_table_t

    def __init__(self, store: Store, ty: TableType, init: IntoVal):
        """
        Creates a new table within `store` with the specified `ty`.
        """

        init_val = Val._convert(ty.element, init)

        table = ffi.wasmtime_table_t()
        error = ffi.wasmtime_table_new(store._context, ty._ptr, byref(init_val._unwrap_raw()), byref(table))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._table = table

    @classmethod
    def _from_raw(cls, table: ffi.wasmtime_table_t) -> "Table":
        ty: "Table" = cls.__new__(cls)
        ty._table = table
        return ty

    def type(self, store: Storelike) -> TableType:
        """
        Gets the type of this table as a `TableType`
        """

        ptr = ffi.wasmtime_table_type(store._context, byref(self._table))
        return TableType._from_ptr(ptr, None)

    def size(self, store: Storelike) -> int:
        """
        Gets the size, in elements, of this table
        """
        return ffi.wasmtime_table_size(store._context, byref(self._table))

    def grow(self, store: Storelike, amt: int, init: IntoVal) -> int:
        """
        Grows this table by the specified number of slots, using the specified
        initializer for all new table slots.

        Raises a `WasmtimeError` if the table could not be grown.
        Returns the previous size of the table otherwise.
        """
        init_val = Val._convert(self.type(store).element, init)
        prev = c_uint32(0)
        error = ffi.wasmtime_table_grow(store._context, byref(self._table), c_uint32(amt), byref(init_val._unwrap_raw()), byref(prev))
        if error:
            raise WasmtimeError._from_ptr(error)
        return prev.value

    def get(self, store: Store, idx: int) -> Optional[Any]:
        """
        Gets an individual element within this table.

        Returns `None` for null references in the table (i.e. a null `funcref`
        or a null `externref).

        Returns a `Func` for non-null `funcref` table elements.

        Returns the wrapped extern data for non-null `externref` table elements.

        Returns `None` if `idx` is out of bounds.
        """
        raw = ffi.wasmtime_val_t()
        ok = ffi.wasmtime_table_get(store._context, byref(self._table), idx, byref(raw))
        if not ok:
            return None
        val = Val(raw)
        if val.value:
            return val.value
        else:
            return val

    def set(self, store: Store, idx: int, val: IntoVal) -> None:
        """
        Sets an individual element within this table.

        `idx` must be an integer index.

        The `val` specified must be convertible into this table's element
        type. I.e. for a `funcref` table, `val` must either be a `Func` or
        `None`, and for an `externref` table, `val` may be any arbitrary
        external data.

        Raises a `WasmtimeError` if `idx` is out of bounds.
        """
        value = Val._convert(self.type(store).element, val)
        error = ffi.wasmtime_table_set(store._context, byref(self._table), idx, byref(value._unwrap_raw()))
        if error:
            raise WasmtimeError._from_ptr(error)

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(table=self._table)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_TABLE, union)
