from .ffi import *
from ctypes import *

dll.wasmtime_wat2wasm.restype = c_bool


def wat2wasm(wat):
    wat = wat.encode('utf8')
    wat_buffer = cast(create_string_buffer(wat), POINTER(c_uint8))
    wat = wasm_byte_vec_t(len(wat), wat_buffer)
    wasm = wasm_byte_vec_t()
    error = wasm_byte_vec_t()
    ok = dll.wasmtime_wat2wasm(byref(wat), byref(wasm), byref(error))
    if ok:
        ret = wasm.to_bytes()
        dll.wasm_byte_vec_delete(byref(wasm))
        return ret
    else:
        raise RuntimeError(error.to_str())
