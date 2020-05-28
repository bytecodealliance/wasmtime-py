__all__ = [
    "wat2wasm",
]

from ctypes import cast, create_string_buffer, POINTER, c_uint8, byref

from ._error import WasmtimeError
from ._ffi import dll, P_wasmtime_error_t, wasm_byte_vec_t

dll.wasmtime_wat2wasm.restype = P_wasmtime_error_t


def wat2wasm(wat):
    """
    Converts the [WebAssembly Text format][wat] to the binary format.

    This function is intended to be a convenience function for local
    development and you likely don't want to use it extensively in production.
    It's much faster to parse and compile the binary format than it is to
    process the text format.

    Takes a `str` as input, raises an error if it fails to parse, and returns
    a `bytes` if conversion/parsing was successful.

    >>> wat2wasm('(module)')
    bytearray(b'\\x00asm\\x01\\x00\\x00\\x00')

    [wat]: https://webassembly.github.io/spec/core/text/index.html
    """

    if isinstance(wat, str):
        wat = wat.encode('utf8')
    wat_buffer = cast(create_string_buffer(wat), POINTER(c_uint8))
    wat = wasm_byte_vec_t(len(wat), wat_buffer)
    wasm = wasm_byte_vec_t()
    error = dll.wasmtime_wat2wasm(byref(wat), byref(wasm))
    if error:
        raise WasmtimeError.__from_ptr__(error)
    else:
        ret = wasm.to_bytes()
        dll.wasm_byte_vec_delete(byref(wasm))
        return ret
