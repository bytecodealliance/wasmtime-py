import ctypes

from . import _ffi as ffi
from wasmtime import WasmtimeError
import typing


def wat2wasm(wat: typing.Union[str, bytes]) -> bytearray:
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
    wat_buffer = ctypes.create_string_buffer(wat)
    wasm = ffi.wasm_byte_vec_t()
    error = ffi.wasmtime_wat2wasm(wat_buffer, len(wat), ctypes.byref(wasm))
    if error:
        raise WasmtimeError._from_ptr(error)
    else:
        ret = ffi.to_bytes(wasm)
        ffi.wasm_byte_vec_delete(ctypes.byref(wasm))
        return ret

def _to_wasm(wasm: typing.Union[str, bytes, bytearray]) -> typing.Union[bytes, bytearray]:
    # If this looks like a string, parse it as the text format. Note that
    # in python 2 strings and bytes are basically the same, so we skip this
    # if the first byte in the string is 0, meaning this is actually a wasm
    # module.
    if isinstance(wasm, str) and len(wasm) > 0 and ord(wasm[0]) != 0:
        wasm = wat2wasm(wasm)
    if isinstance(wasm, bytes) and len(wasm) > 0 and wasm[0] != 0:
        wasm = wat2wasm(wasm)

    if not isinstance(wasm, (bytes, bytearray)):
        raise TypeError("expected wasm bytes")
    return wasm
