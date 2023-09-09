from ctypes import *
from pathlib import Path
import ctypes
import sys
import platform
import typing

if sys.maxsize <= 2**32:
    raise RuntimeError("wasmtime only works on 64-bit platforms right now")

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
if machine == 'arm64':
    machine = 'aarch64'
if machine != 'x86_64' and machine != 'aarch64':
    raise RuntimeError("unsupported architecture for wasmtime: {}".format(machine))

filename = Path(__file__).parent / (sys.platform + '-' + machine) / libname
if not filename.exists():
    raise RuntimeError("precompiled wasmtime binary not found at `{}`".format(filename))
dll = cdll.LoadLibrary(str(filename))

WASM_I32 = c_uint8(0)
WASM_I64 = c_uint8(1)
WASM_F32 = c_uint8(2)
WASM_F64 = c_uint8(3)
WASM_ANYREF = c_uint8(128)
WASM_FUNCREF = c_uint8(129)
# WASM_V128 = c_uint8(4)

WASMTIME_I32 = c_uint8(0)
WASMTIME_I64 = c_uint8(1)
WASMTIME_F32 = c_uint8(2)
WASMTIME_F64 = c_uint8(3)
WASMTIME_V128 = c_uint8(4)
WASMTIME_FUNCREF = c_uint8(5)
WASMTIME_EXTERNREF = c_uint8(6)

WASM_CONST = c_uint8(0)
WASM_VAR = c_uint8(1)

WASMTIME_EXTERN_FUNC = c_uint8(0)
WASMTIME_EXTERN_GLOBAL = c_uint8(1)
WASMTIME_EXTERN_TABLE = c_uint8(2)
WASMTIME_EXTERN_MEMORY = c_uint8(3)
WASMTIME_EXTERN_INSTANCE = c_uint8(4)
WASMTIME_EXTERN_MODULE = c_uint8(5)

WASMTIME_FUNCREF_NULL = (1 << 64) - 1


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
    ref: "typing.Union[ctypes._Pointer[wasm_ref_t], None]"


class wasm_val_t(Structure):
    _fields_ = [("kind", c_uint8), ("of", wasm_val_union)]

    kind: int
    of: wasm_val_union


from ._bindings import *  # noqa


def to_bytes(vec: wasm_byte_vec_t) -> bytearray:
    ty = c_uint8 * vec.size
    return bytearray(ty.from_address(addressof(vec.data.contents)))


def to_str(vec: wasm_byte_vec_t) -> str:
    return to_bytes(vec).decode("utf-8")


def to_str_raw(ptr: "ctypes._Pointer", size: int) -> str:
    return string_at(ptr, size).decode("utf-8")


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
