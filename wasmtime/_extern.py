from ._ffi import *
from ctypes import *

dll.wasm_extern_as_func.restype = P_wasm_func_t
dll.wasm_extern_as_table.restype = P_wasm_table_t
dll.wasm_extern_as_global.restype = P_wasm_global_t
dll.wasm_extern_as_memory.restype = P_wasm_memory_t
dll.wasm_extern_type.restype = P_wasm_externtype_t


def wrap_extern(ptr, owner):
    from wasmtime import Func, Table, Global, Memory

    if not isinstance(ptr, P_wasm_extern_t):
        raise TypeError("wrong pointer type")

    # We must free this as an extern, so if there's no ambient owner then
    # configure an owner with the right destructor
    if owner is None:
        owner = Extern(ptr)

    val = dll.wasm_extern_as_func(ptr)
    if val:
        return Func.__from_ptr__(val, owner)
    val = dll.wasm_extern_as_table(ptr)
    if val:
        return Table.__from_ptr__(val, owner)
    val = dll.wasm_extern_as_global(ptr)
    if val:
        return Global.__from_ptr__(val, owner)
    val = dll.wasm_extern_as_memory(ptr)
    assert(val)
    return Memory.__from_ptr__(val, owner)


def get_extern_ptr(item):
    from wasmtime import Func, Table, Global, Memory

    if isinstance(item, Func):
        return item._as_extern()
    elif isinstance(item, Global):
        return item._as_extern()
    elif isinstance(item, Memory):
        return item._as_extern()
    elif isinstance(item, Table):
        return item._as_extern()
    else:
        raise TypeError("expected a Func, Global, Memory, or Table")


class Extern:
    def __init__(self, ptr):
        self.ptr = ptr

    def __del__(self):
        dll.wasm_extern_delete(self.ptr)
