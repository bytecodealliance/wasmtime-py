from . import _ffi as ffi
from ctypes import *
from ._exportable import AsExtern
from typing import Optional, Any


def wrap_extern(ptr: pointer, owner: Optional[Any]) -> AsExtern:
    from wasmtime import Func, Table, Global, Memory

    if not isinstance(ptr, POINTER(ffi.wasm_extern_t)):
        raise TypeError("wrong pointer type")

    # We must free this as an extern, so if there's no ambient owner then
    # configure an owner with the right destructor
    if owner is None:
        owner = Extern(ptr)

    val = ffi.wasm_extern_as_func(ptr)
    if val:
        return Func.__from_ptr__(val, owner)
    val = ffi.wasm_extern_as_table(ptr)
    if val:
        return Table.__from_ptr__(val, owner)
    val = ffi.wasm_extern_as_global(ptr)
    if val:
        return Global.__from_ptr__(val, owner)
    val = ffi.wasm_extern_as_memory(ptr)
    assert(val)
    return Memory.__from_ptr__(val, owner)


def get_extern_ptr(item: AsExtern) -> pointer:
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
    def __init__(self, ptr: pointer):
        self.ptr = ptr

    def __del__(self):
        ffi.wasm_extern_delete(self.ptr)
