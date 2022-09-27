from . import _ffi as ffi
import ctypes
from ._exportable import AsExtern
from wasmtime import WasmtimeError


def wrap_extern(ptr: ffi.wasmtime_extern_t) -> AsExtern:
    from wasmtime import Func, Table, Global, Memory, Module, Instance

    if ptr.kind == ffi.WASMTIME_EXTERN_FUNC.value:
        return Func._from_raw(ptr.of.func)
    if ptr.kind == ffi.WASMTIME_EXTERN_TABLE.value:
        return Table._from_raw(ptr.of.table)
    if ptr.kind == ffi.WASMTIME_EXTERN_GLOBAL.value:
        return Global._from_raw(ptr.of.global_)
    if ptr.kind == ffi.WASMTIME_EXTERN_MEMORY.value:
        return Memory._from_raw(ptr.of.memory)
    if ptr.kind == ffi.WASMTIME_EXTERN_INSTANCE.value:
        return Instance._from_raw(ptr.of.instance)
    if ptr.kind == ffi.WASMTIME_EXTERN_MODULE.value:
        return Module._from_ptr(ptr.of.module)
    raise WasmtimeError("unknown extern")


def get_extern_ptr(item: AsExtern) -> ffi.wasmtime_extern_t:
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
    def __init__(self, ptr: "ctypes._Pointer[ffi.wasm_extern_t]"):
        self.ptr = ptr

    def __del__(self) -> None:
        ffi.wasm_extern_delete(self.ptr)
