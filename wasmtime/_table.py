from . import _ffi as ffi
from ctypes import *
from wasmtime import TableType, Store, Func, WasmtimeError


def get_func_ptr(init):
    if init is None:
        return None
    elif isinstance(init, Func):
        return init.__ptr__
    else:
        raise TypeError("expected a `Func` or `None`")


class Table:
    def __init__(self, store, ty, init):
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
        error = ffi.wasmtime_funcref_table_new(store.__ptr__, ty.__ptr__, init_ptr, byref(ptr))
        if error:
            raise WasmtimeError.__from_ptr__(error)
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_table_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def type(self):
        """
        Gets the type of this table as a `TableType`
        """

        ptr = ffi.wasm_table_type(self.__ptr__)
        return TableType.__from_ptr__(ptr, None)

    @property
    def size(self):
        """
        Gets the size, in elements, of this table
        """

        return ffi.wasm_table_size(self.__ptr__)

    def grow(self, amt, init):
        """
        Grows this table by the specified number of slots, using the specified
        initializer for all new table slots.

        Raises a `WasmtimeError` if the table could not be grown.
        Returns the previous size of the table otherwise.
        """
        init_ptr = get_func_ptr(init)

        prev = c_uint32(0)
        error = ffi.wasmtime_funcref_table_grow(self.__ptr__, c_uint32(amt), init_ptr, byref(prev))
        if error:
            raise WasmtimeError("failed to grow table")
        return prev.value

    def __getitem__(self, idx):
        """
        Gets an individual element within this table. Currently only works on
        `funcref` tables.

        Returns `None` for a slot where no function has been placed into.
        Returns `Func` for a slot with a function.
        Raises an `WasmtimeError` if `idx` is out of bounds.
        """

        idx = c_uint32(idx)
        ptr = POINTER(ffi.wasm_func_t)()
        ok = ffi.wasmtime_funcref_table_get(self.__ptr__, idx, byref(ptr))
        if ok:
            if ptr:
                return Func.__from_ptr__(ptr, None)
            return None
        raise WasmtimeError("table index out of bounds")

    def __setitem__(self, idx, val):
        """
        Sets an individual element within this table. Currently only works on
        `funcref` tables.

        The `val` specified must either be a `Func` or `None`, and `idx` must
        be an integer index.

        Raises a `WasmtimeError` if `idx` is out of bounds.
        """

        idx = c_uint32(idx)
        val_ptr = get_func_ptr(val)
        error = ffi.wasmtime_funcref_table_set(self.__ptr__, idx, val_ptr)
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def _as_extern(self):
        return ffi.wasm_table_as_extern(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_table_delete(self.__ptr__)
