from pathlib import Path
import ctypes
import sys
import platform
import typing

if sys.maxsize <= 2**32:
    raise RuntimeError("wasmtime only works on 64-bit platforms right now")

sys_platform = sys.platform

# For Python versions <=3.12. 3.13+ supports PEP 738 and uses sys.platform
if hasattr(sys, 'getandroidapilevel'):
    sys_platform = 'android'

if sys_platform == 'linux' or sys_platform == 'android':
    libname = '_libwasmtime.so'
elif sys_platform == 'win32':
    libname = '_wasmtime.dll'
elif sys_platform == 'darwin':
    libname = '_libwasmtime.dylib'
else:
    raise RuntimeError("unsupported platform `{}` for wasmtime".format(sys_platform))


machine = platform.machine()
if machine == 'AMD64':
    machine = 'x86_64'
if machine == 'arm64' or machine == 'ARM64':
    machine = 'aarch64'
if machine != 'x86_64' and machine != 'aarch64':
    raise RuntimeError("unsupported architecture for wasmtime: {}".format(machine))

filename = Path(__file__).parent / (sys_platform + '-' + machine) / libname

dll = ctypes.cdll.LoadLibrary(str(filename))

WASM_I32 = ctypes.c_uint8(0)
WASM_I64 = ctypes.c_uint8(1)
WASM_F32 = ctypes.c_uint8(2)
WASM_F64 = ctypes.c_uint8(3)
WASM_ANYREF = ctypes.c_uint8(128)
WASM_FUNCREF = ctypes.c_uint8(129)
# WASM_V128 = ctypes.c_uint8(4)

WASMTIME_I32 = ctypes.c_uint8(0)
WASMTIME_I64 = ctypes.c_uint8(1)
WASMTIME_F32 = ctypes.c_uint8(2)
WASMTIME_F64 = ctypes.c_uint8(3)
WASMTIME_V128 = ctypes.c_uint8(4)
WASMTIME_FUNCREF = ctypes.c_uint8(5)
WASMTIME_EXTERNREF = ctypes.c_uint8(6)

WASM_CONST = ctypes.c_uint8(0)
WASM_VAR = ctypes.c_uint8(1)

WASMTIME_EXTERN_FUNC = ctypes.c_uint8(0)
WASMTIME_EXTERN_GLOBAL = ctypes.c_uint8(1)
WASMTIME_EXTERN_TABLE = ctypes.c_uint8(2)
WASMTIME_EXTERN_MEMORY = ctypes.c_uint8(3)
WASMTIME_EXTERN_SHAREDMEMORY = ctypes.c_uint8(4)
WASMTIME_EXTERN_INSTANCE = ctypes.c_uint8(4)
WASMTIME_EXTERN_MODULE = ctypes.c_uint8(5)

WASMTIME_FUNCREF_NULL = (1 << 64) - 1


class wasm_ref_t(ctypes.Structure):
    pass


class wasm_val_union(ctypes.Union):
    _fields_ = [
        ("i32", ctypes.c_int32),
        ("i64", ctypes.c_int64),
        ("f32", ctypes.c_float),
        ("f64", ctypes.c_double),
        ("ref", ctypes.POINTER(wasm_ref_t)),
    ]

    i32: int
    i64: int
    f32: float
    f64: float
    ref: "typing.Union[ctypes._Pointer[wasm_ref_t], None]"


class wasm_val_t(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_uint8), ("of", wasm_val_union)]

    kind: int
    of: wasm_val_union


from ._bindings import wasm_byte_vec_t  # noqa


def to_bytes(vec: wasm_byte_vec_t) -> bytearray:
    ty = ctypes.c_uint8 * vec.size
    return bytearray(ty.from_address(ctypes.addressof(vec.data.contents)))


def to_str(vec: wasm_byte_vec_t) -> str:
    return to_bytes(vec).decode("utf-8")


def to_str_raw(ptr: "ctypes._Pointer", size: int) -> str:
    return ctypes.string_at(ptr, size).decode("utf-8")


def str_to_name(s: str, trailing_nul: bool = False) -> wasm_byte_vec_t:
    if not isinstance(s, str):
        raise TypeError("expected a string")
    s_bytes = s.encode('utf8')
    buf = ctypes.cast(ctypes.create_string_buffer(s_bytes), ctypes.POINTER(ctypes.c_uint8))
    if trailing_nul:
        extra = 1
    else:
        extra = 0
    return wasm_byte_vec_t(len(s_bytes) + extra, buf)
