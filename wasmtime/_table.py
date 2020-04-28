from ._ffi import *
from ctypes import *
from wasmtime import TableType

dll.wasm_table_as_extern.restype = P_wasm_extern_t
dll.wasm_table_type.restype = P_wasm_tabletype_t
dll.wasm_table_size.restype = c_uint32


class Table(object):
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_table_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def type(self):
        """
        Gets the type of this table as a `TableType`
        """

        ptr = dll.wasm_table_type(self.__ptr__)
        return TableType.__from_ptr__(ptr, None)

    @property
    def size(self):
        """
        Gets the size, in elements, of this table
        """

        return dll.wasm_table_size(self.__ptr__)

    def _as_extern(self):
        return dll.wasm_table_as_extern(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_table_delete(self.__ptr__)
