from ctypes import *
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
WASMTIME_EXTERN_SHAREDMEMORY = c_uint8(4)

WASMTIME_FUNCREF_NULL = (1 << 64) - 1

WASMTIME_COMPONENT_ITEM_COMPONENT = c_uint8(0)
WASMTIME_COMPONENT_ITEM_COMPONENT_INSTANCE = c_uint8(1)
WASMTIME_COMPONENT_ITEM_MODULE = c_uint8(2)
WASMTIME_COMPONENT_ITEM_COMPONENT_FUNC = c_uint8(3)
WASMTIME_COMPONENT_ITEM_RESOURCE = c_uint8(4)
WASMTIME_COMPONENT_ITEM_CORE_FUNC = c_uint8(5)
WASMTIME_COMPONENT_ITEM_TYPE = c_uint8(6)

WASMTIME_COMPONENT_VALTYPE_BOOL = c_uint8(0)
WASMTIME_COMPONENT_VALTYPE_S8 = c_uint8(1)
WASMTIME_COMPONENT_VALTYPE_S16 = c_uint8(2)
WASMTIME_COMPONENT_VALTYPE_S32 = c_uint8(3)
WASMTIME_COMPONENT_VALTYPE_S64 = c_uint8(4)
WASMTIME_COMPONENT_VALTYPE_U8 = c_uint8(5)
WASMTIME_COMPONENT_VALTYPE_U16 = c_uint8(6)
WASMTIME_COMPONENT_VALTYPE_U32 = c_uint8(7)
WASMTIME_COMPONENT_VALTYPE_U64 = c_uint8(8)
WASMTIME_COMPONENT_VALTYPE_F32 = c_uint8(9)
WASMTIME_COMPONENT_VALTYPE_F64 = c_uint8(10)
WASMTIME_COMPONENT_VALTYPE_CHAR = c_uint8(11)
WASMTIME_COMPONENT_VALTYPE_STRING = c_uint8(12)
WASMTIME_COMPONENT_VALTYPE_LIST = c_uint8(13)
WASMTIME_COMPONENT_VALTYPE_RECORD = c_uint8(14)
WASMTIME_COMPONENT_VALTYPE_TUPLE = c_uint8(15)
WASMTIME_COMPONENT_VALTYPE_VARIANT = c_uint8(16)
WASMTIME_COMPONENT_VALTYPE_ENUM = c_uint8(17)
WASMTIME_COMPONENT_VALTYPE_OPTION = c_uint8(18)
WASMTIME_COMPONENT_VALTYPE_RESULT = c_uint8(19)
WASMTIME_COMPONENT_VALTYPE_FLAGS = c_uint8(20)
WASMTIME_COMPONENT_VALTYPE_OWN = c_uint8(21)
WASMTIME_COMPONENT_VALTYPE_BORROW = c_uint8(22)
WASMTIME_COMPONENT_VALTYPE_FUTURE = c_uint8(23)
WASMTIME_COMPONENT_VALTYPE_STREAM = c_uint8(24)
WASMTIME_COMPONENT_VALTYPE_ERROR_CONTEXT = c_uint8(25)

WASMTIME_COMPONENT_BOOL = c_uint8(0)
WASMTIME_COMPONENT_S8 = c_uint8(1)
WASMTIME_COMPONENT_U8 = c_uint8(2)
WASMTIME_COMPONENT_S16 = c_uint8(3)
WASMTIME_COMPONENT_U16 = c_uint8(4)
WASMTIME_COMPONENT_S32 = c_uint8(5)
WASMTIME_COMPONENT_U32 = c_uint8(6)
WASMTIME_COMPONENT_S64 = c_uint8(7)
WASMTIME_COMPONENT_U64 = c_uint8(8)
WASMTIME_COMPONENT_F32 = c_uint8(9)
WASMTIME_COMPONENT_F64 = c_uint8(10)
WASMTIME_COMPONENT_CHAR = c_uint8(11)
WASMTIME_COMPONENT_STRING = c_uint8(12)
WASMTIME_COMPONENT_LIST = c_uint8(13)
WASMTIME_COMPONENT_RECORD = c_uint8(14)
WASMTIME_COMPONENT_TUPLE = c_uint8(15)
WASMTIME_COMPONENT_VARIANT = c_uint8(16)
WASMTIME_COMPONENT_ENUM = c_uint8(17)
WASMTIME_COMPONENT_OPTION = c_uint8(18)
WASMTIME_COMPONENT_RESULT = c_uint8(19)
WASMTIME_COMPONENT_FLAGS = c_uint8(20)
WASMTIME_COMPONENT_RESOURCE = c_uint8(21)

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


def str_to_capi(s: str) -> wasm_byte_vec_t:
    if not isinstance(s, str):
        raise TypeError("expected a string")
    return bytes_to_capi(s.encode('utf8'))

def bytes_to_capi(s: typing.Union[bytes, bytearray]) -> wasm_byte_vec_t:
    if not isinstance(s, (bytes, bytearray)):
        raise TypeError("expected bytes or bytearray")
    vec = wasm_byte_vec_t()
    wasm_byte_vec_new_uninitialized(byref(vec), len(s))
    buf = (c_uint8 * len(s)).from_buffer_copy(s)
    ctypes.memmove(vec.data, buf, len(s))
    return vec

def take_pointer(structure: ctypes._Pointer, field_name: str) -> ctypes._Pointer:
    """
    Moral equivalent of `mem::replace(&mut structure.field_name, NULL)`

    Ctypes explicitly documents "Surprises" which includes, for example:

            import ctypes

            class A(ctypes.Structure):
                _fields_ = [("x", ctypes.POINTER(ctypes.c_int))]

            x_p = ctypes.pointer(ctypes.c_int(3))
            a = A(x_p)
            x = a.x

            print(x.contents)
            a.x = None
            print(x.contents)

    This program will segfault on the second access. It turns out that `x = a.x`
    is still actually a pointer into the original structure, and `a.x`
    overwrites that field so accessing `x` later accesses null memory. This
    method is an attempt to work around this surprising behavior and actually
    read the field from a structure and replace it with null.

    I'll be honest I just sat through a 3 hour flight, a 5 hour layover, a 9
    hour flight, 1 hour train ride, and I'm sitting in a hotel lobby for
    another 5 hours. That's my state of mind writing this up, so please
    draw conclusions about this method as appropriate.
    """
    field = getattr(structure, field_name)
    assert(isinstance(field, ctypes._Pointer))
    ret = ctypes.cast(ctypes.addressof(field.contents), ctypes.POINTER(field._type_))
    setattr(structure, field_name, None)
    return ret
