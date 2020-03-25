from .ffi import *
from ctypes import *
from wasmtime import Store, TableType, Val, Extern

dll.wasm_table_as_extern.restype = P_wasm_extern_t
dll.wasm_table_type.restype = P_wasm_tabletype_t
dll.wasm_table_size.restype = c_uint32

class Table:
#     # Creates a new table in `store` with the given `ty`. The `init` value
#     # fills in the initial slots in the table, an can be `None` for null.
#     def __init__(self, store, ty, init):
#         if not isinstance(store, Store):
#             raise TypeError("expected a Store")
#         if not isinstance(ty, TableType):
#             raise TypeError("expected a TableType")
#         if init is not None and not isinstance(init, Val):
#             raise TypeError("expected a Val")
#         if init is not None:
#             init = byref(init.__raw__)
#         ptr = dll.wasm_table_new(store.__ptr__, ty.__ptr__, init)
#         if ptr == 0:
#             raise RuntimeError("failed to create table")
#         self.__ptr__ = cast(ptr, P_wasm_table_t)
#         self.store = store

    # Gets the type of this table as a `TableType`
    def type(self):
        ptr = dll.wasm_table_type(self.__ptr__)
        return TableType.__from_ptr__(ptr, None)

    # Gets the size, in elements, of this table
    def size(self):
        return dll.wasm_table_size(self.__ptr__)

#     # Gets the current value of this table
#     def get(self, idx):
#         raw = wasm_val_t()
#         dll.wasm_table_get(self.__ptr__, byref(raw))
#         return Val(raw)
#
#     # Sets the value of this table to a new value
#     def set(self, idx, val):
#         if not isinstance(val, Val):
#             raise TypeError("expected a Val")
#         dll.wasm_table_set(self.__ptr__, byref(val.__raw__))
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_table_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Returns this as an instance of `Extern`
    def as_extern(self):
        ptr = dll.wasm_table_as_extern(self.__ptr__)
        return Extern.__from_ptr__(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_table_delete(self.__ptr__)
