from . import _ffi as ffi
from ctypes import *
from ._exportable import AsExtern
from typing import Optional, Any
from wasmtime import WasmtimeError


def wrap_extern(ptr: 'pointer[ffi.wasm_extern_t]', owner: Optional[Any]) -> AsExtern:
    from wasmtime import Func, Table, Global, Memory, Module, Instance

    if not isinstance(ptr, POINTER(ffi.wasm_extern_t)):
        raise TypeError("wrong pointer type")

    # We must free this as an extern, so if there's no ambient owner then
    # configure an owner with the right destructor
    if owner is None:
        owner = Extern(ptr)

    val = ffi.wasm_extern_as_func(ptr)
    if val:
        return Func._from_ptr(val, owner)
    val = ffi.wasm_extern_as_table(ptr)
    if val:
        return Table._from_ptr(val, owner)
    val = ffi.wasm_extern_as_global(ptr)
    if val:
        return Global._from_ptr(val, owner)
    val = ffi.wasm_extern_as_memory(ptr)
    if val:
        return Memory._from_ptr(val, owner)
    val = ffi.wasm_extern_as_instance(ptr)
    if val:
        return Instance._from_ptr(val, owner)
    val = ffi.wasm_extern_as_module(ptr)
    if val:
        return Module._from_ptr(val, owner)
    raise WasmtimeError("unknown extern")


def get_extern_ptr(item: AsExtern) -> "pointer[ffi.wasm_extern_t]":
    from wasmtime import Func, Table, Global, Memory, Module, Instance

    if isinstance(item, Func):
        return item._as_extern()
    elif isinstance(item, Global):
        return item._as_extern()
    elif isinstance(item, Memory):
        return item._as_extern()
    elif isinstance(item, Table):
        return item._as_extern()
    elif isinstance(item, Module):
        return item._as_extern()
    elif isinstance(item, Instance):
        return item._as_extern()
    else:
        raise TypeError("expected a Func, Global, Memory, Table, Module, or Instance")


class Extern:
    def __init__(self, ptr: "pointer[ffi.wasm_extern_t]"):
        self.ptr = ptr

    def __del__(self) -> None:
        ffi.wasm_extern_delete(self.ptr)
