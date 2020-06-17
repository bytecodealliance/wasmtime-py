from ctypes import byref, POINTER


class WasmtimeError(Exception):
    def __init__(self, message):
        self.message = message

    @classmethod
    def __from_ptr__(cls, ptr):
        from . import _ffi as ffi
        if not isinstance(ptr, POINTER(ffi.wasmtime_error_t)):
            raise TypeError("wrong pointer type")
        message_vec = ffi.wasm_byte_vec_t()
        ffi.wasmtime_error_message(ptr, byref(message_vec))
        message = ffi.to_str(message_vec)
        ffi.wasm_byte_vec_delete(byref(message_vec))
        ffi.wasmtime_error_delete(ptr)
        return WasmtimeError(message)

    def __str__(self):
        return self.message
