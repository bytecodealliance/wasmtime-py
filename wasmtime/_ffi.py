from ctypes import *
import os
import sys
import platform
import typing

from wasmtime import WasmtimeError

if sys.maxsize <= 2**32:
    raise WasmtimeError("wasmtime only works on 64-bit platforms right now")

if sys.platform == 'linux':
    libname = '_libwasmtime.so'
elif sys.platform == 'win32':
    libname = '_wasmtime.dll'
elif sys.platform == 'darwin':
    libname = '_libwasmtime.dylib'
else:
    raise RuntimeError("unsupported platform `{}` for wasmtime".format(sys.platform))

machine = platform.machine()
if machine == 'AMD64':
    machine = 'x86_64'
if machine != 'x86_64' and machine != 'aarch64':
    raise RuntimeError("unsupported architecture for wasmtime: {}".format(machine))

filename = os.path.join(os.path.dirname(__file__), sys.platform + '-' + machine, libname)
if not os.path.exists(filename):
    raise RuntimeError("precompiled wasmtime binary not found at `{}`".format(filename))
dll = cdll.LoadLibrary(filename)

WASM_I32 = c_uint8(0)
WASM_I64 = c_uint8(1)
WASM_F32 = c_uint8(2)
WASM_F64 = c_uint8(3)
WASM_ANYREF = c_uint8(128)
WASM_FUNCREF = c_uint8(129)

WASM_CONST = c_uint8(0)
WASM_VAR = c_uint8(1)


class wasm_ref_t(Structure):
    pass


class wasm_val_union(Union):
    _fields_ = [
        ("i32", c_int32),
        ("i64", c_int64),
        ("f32", c_float),
        ("f64", c_double),
        ("ref", POINTER(wasm_ref_t)),
    ]

    i32: int
    i64: int
    f32: float
    f64: float
    ref: "typing.Union[pointer[wasm_ref_t], None]"


class wasm_val_t(Structure):
    _fields_ = [("kind", c_uint8), ("of", wasm_val_union)]

    kind: int
    of: wasm_val_union


from ._bindings import * # noqa


def to_bytes(vec: wasm_byte_vec_t) -> bytearray:
    ty = c_uint8 * vec.size
    return bytearray(ty.from_address(addressof(vec.data.contents)))


def to_str(vec: wasm_byte_vec_t) -> str:
    return to_bytes(vec).decode("utf-8")


def str_to_name(s: str, trailing_nul: bool = False) -> wasm_byte_vec_t:
    if not isinstance(s, str):
        raise TypeError("expected a string")
    s_bytes = s.encode('utf8')
    buf = cast(create_string_buffer(s_bytes), POINTER(c_uint8))
    if trailing_nul:
        extra = 1
    else:
        extra = 0
    return wasm_byte_vec_t(len(s_bytes) + extra, buf)
