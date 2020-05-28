__all__ = [
    "WasmtimeError",
]

from ctypes import byref


class WasmtimeError(Exception):
    def __init__(self, message):
        self.message = message

    @classmethod
    def __from_ptr__(cls, ptr):
        from ._ffi import dll, P_wasmtime_error_t, wasm_byte_vec_t
        if not isinstance(ptr, P_wasmtime_error_t):
            raise TypeError("wrong pointer type")
        message_vec = wasm_byte_vec_t()
        dll.wasmtime_error_message(ptr, byref(message_vec))
        message = message_vec.to_str()
        dll.wasm_byte_vec_delete(byref(message_vec))
        dll.wasmtime_error_delete(ptr)
        return WasmtimeError(message)

    def __str__(self):
        return self.message
