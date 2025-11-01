from . import _ffi as ffi
import ctypes
from ._exportable import AsExtern
from wasmtime import WasmtimeError, Managed


def wrap_extern(ptr: ffi.wasmtime_extern_t) -> AsExtern:
    from wasmtime import Func, Table, Global, Memory, SharedMemory

    if ptr.kind == ffi.WASMTIME_EXTERN_FUNC.value:
        return Func._from_raw(ptr.of.func)
    if ptr.kind == ffi.WASMTIME_EXTERN_TABLE.value:
        return Table._from_raw(ptr.of.table)
    if ptr.kind == ffi.WASMTIME_EXTERN_GLOBAL.value:
        return Global._from_raw(ptr.of.global_)
    if ptr.kind == ffi.WASMTIME_EXTERN_MEMORY.value:
        return Memory._from_raw(ptr.of.memory)
    if ptr.kind == ffi.WASMTIME_EXTERN_SHAREDMEMORY.value:
        return SharedMemory._from_ptr(ptr.of.sharedmemory)
    raise WasmtimeError("unknown extern")


def get_extern_ptr(item: AsExtern) -> ffi.wasmtime_extern_t:
    from wasmtime import Func, Table, Global, Memory, SharedMemory

    if isinstance(item, Func):
        return item._as_extern()
    elif isinstance(item, Global):
        return item._as_extern()
    elif isinstance(item, Memory):
        return item._as_extern()
    elif isinstance(item, SharedMemory):
        return item._as_extern()
    elif isinstance(item, Table):
        return item._as_extern()
    else:
        raise TypeError("expected a Func, Global, Memory, or Table")


class Extern(Managed["ctypes._Pointer[ffi.wasm_extern_t]"]):
    def __init__(self, ptr: "ctypes._Pointer[ffi.wasm_extern_t]"):
        self._set_ptr(ptr)

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_extern_t]") -> None:
        ffi.wasm_extern_delete(ptr)
