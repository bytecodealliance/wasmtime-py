from ._ffi import *
from ctypes import *
from wasmtime import TableType, Extern

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

    def type(self):
        """
        Gets the type of this table as a `TableType`
        """

        ptr = dll.wasm_table_type(self.__ptr__)
        return TableType.__from_ptr__(ptr, None)

    def size(self):
        """
        Gets the size, in elements, of this table
        """

        return dll.wasm_table_size(self.__ptr__)

    def as_extern(self):
        """
        Returns this as an instance of `Extern`
        """

        ptr = dll.wasm_table_as_extern(self.__ptr__)
        return Extern.__from_ptr__(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_table_delete(self.__ptr__)
