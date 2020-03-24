from .ffi import *
from ctypes import *
from wasmtime import Engine

def wat2wasm(engine, wat):
    if not isinstance(engine, Engine):
        raise TypeError("expected Engine")
    wat = wat.encode('utf8')
    wat_buffer = cast(create_string_buffer(wat), POINTER(c_uint8))
    wat = wasm_byte_vec_t(len(wat), wat_buffer)
    wasm = wasm_byte_vec_t()
    error = wasm_byte_vec_t()
    ok = c_bool(dll.wasmtime_wat2wasm(engine.__ptr__, byref(wat), byref(wasm), byref(error)))
    if ok:
        ret = bytes(wasm.data[:wasm.size])
        dll.wasm_byte_vec_delete(byref(wasm))
        return ret
    else:
        error = bytes(error.data[:error.size]).decode("utf-8")
        raise RuntimeError(error)
