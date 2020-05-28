from ctypes import *
__all__ = [
    "P_wasi_config_t",
    "P_wasi_instance_t",
    "P_wasm_config_t",
    "P_wasm_engine_t",
    "P_wasm_extern_t",
    "P_wasm_externtype_t",
    "P_wasm_func_t",
    "P_wasm_functype_t",
    "P_wasm_global_t",
    "P_wasm_globaltype_t",
    "P_wasm_memory_t",
    "P_wasm_memorytype_t",
    "P_wasm_store_t",
    "P_wasm_table_t",
    "P_wasm_tabletype_t",
    "P_wasm_trap_t",
    "P_wasm_valtype_t",
    "P_wasmtime_caller_t",
    "P_wasmtime_error_t",
    "P_wasmtime_interrupt_handle_t",
    "P_wasmtime_linker_t",
    "dll",
    "wasm_byte_vec_t",
    "wasm_limits_t",
    "wasm_name_t",
    "wasm_val_t",
    "wasm_valtype_vec_t",
    "str_to_name",
    "P_wasm_instance_t",
    "wasm_extern_vec_t",
    "P_wasm_module_t",
    "wasm_importtype_vec_t",
    "wasm_exporttype_vec_t",
    "P_wasm_frame_t",
    "wasm_frame_vec_t",
    "WASM_I32",
    "WASM_I64",
    "WASM_F32",
    "WASM_F64",
    "WASM_ANYREF",
    "WASM_FUNCREF",
    "WASM_VAR",
    "WASM_CONST",
    "P_wasm_importtype_t",
    "P_wasm_exporttype_t",
]

import os
import sys
import platform

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


class wasm_valtype_t(Structure):
    pass


P_wasm_valtype_t = POINTER(wasm_valtype_t)


class wasm_globaltype_t(Structure):
    pass


P_wasm_globaltype_t = POINTER(wasm_globaltype_t)


class wasm_functype_t(Structure):
    pass


P_wasm_functype_t = POINTER(wasm_functype_t)


class wasm_tabletype_t(Structure):
    pass


P_wasm_tabletype_t = POINTER(wasm_tabletype_t)


class wasm_memorytype_t(Structure):
    pass


P_wasm_memorytype_t = POINTER(wasm_memorytype_t)


class wasm_externtype_t(Structure):
    pass


P_wasm_externtype_t = POINTER(wasm_externtype_t)


class wasm_engine_t(Structure):
    pass


P_wasm_engine_t = POINTER(wasm_engine_t)


class wasm_store_t(Structure):
    pass


P_wasm_store_t = POINTER(wasm_store_t)


class wasm_config_t(Structure):
    pass


P_wasm_config_t = POINTER(wasm_config_t)


class wasm_importtype_t(Structure):
    pass


P_wasm_importtype_t = POINTER(wasm_importtype_t)


class wasm_exporttype_t(Structure):
    pass


P_wasm_exporttype_t = POINTER(wasm_exporttype_t)


class wasm_module_t(Structure):
    pass


P_wasm_module_t = POINTER(wasm_module_t)


class wasm_global_t(Structure):
    pass


P_wasm_global_t = POINTER(wasm_global_t)


class wasm_table_t(Structure):
    pass


P_wasm_table_t = POINTER(wasm_table_t)


class wasm_memory_t(Structure):
    pass


P_wasm_memory_t = POINTER(wasm_memory_t)


class wasm_func_t(Structure):
    pass


P_wasm_func_t = POINTER(wasm_func_t)


class wasm_trap_t(Structure):
    pass


P_wasm_trap_t = POINTER(wasm_trap_t)


class wasm_extern_t(Structure):
    pass


P_wasm_extern_t = POINTER(wasm_extern_t)


class wasm_instance_t(Structure):
    pass


P_wasm_instance_t = POINTER(wasm_instance_t)


class wasmtime_linker_t(Structure):
    pass


P_wasmtime_linker_t = POINTER(wasmtime_linker_t)


class wasmtime_caller_t(Structure):
    pass


P_wasmtime_caller_t = POINTER(wasmtime_caller_t)


class wasi_config_t(Structure):
    pass


P_wasi_config_t = POINTER(wasi_config_t)


class wasi_instance_t(Structure):
    pass


P_wasi_instance_t = POINTER(wasi_instance_t)


class wasm_frame_t(Structure):
    pass


P_wasm_frame_t = POINTER(wasm_frame_t)


class wasmtime_error_t(Structure):
    pass


P_wasmtime_error_t = POINTER(wasmtime_error_t)


class wasmtime_interrupt_handle_t(Structure):
    pass


P_wasmtime_interrupt_handle_t = POINTER(wasmtime_interrupt_handle_t)


class wasm_valtype_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(P_wasm_valtype_t))]


class wasm_limits_t(Structure):
    _fields_ = [("min", c_uint32), ("max", c_uint32)]


class wasm_byte_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(c_uint8))]

    def to_bytes(self):
        ty = c_uint8 * self.size
        return bytearray(ty.from_address(addressof(self.data.contents)))

    def to_str(self):
        return self.to_bytes().decode("utf-8")


wasm_name_t = wasm_byte_vec_t


class wasm_exporttype_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(P_wasm_exporttype_t))]


class wasm_importtype_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(P_wasm_importtype_t))]


class wasm_extern_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(P_wasm_extern_t))]


class wasm_frame_vec_t(Structure):
    _fields_ = [("size", c_size_t), ("data", POINTER(P_wasm_frame_t))]


class wasm_val_union(Union):
    _fields_ = [
        ("i32", c_int32),
        ("i64", c_int64),
        ("f32", c_float),
        ("f64", c_double),
    ]


class wasm_val_t(Structure):
    _fields_ = [("kind", c_uint8), ("of", wasm_val_union)]


def str_to_name(s, trailing_nul=False):
    if not isinstance(s, str):
        raise TypeError("expected a string")
    s = s.encode('utf8')
    buf = cast(create_string_buffer(s), POINTER(c_uint8))
    if trailing_nul:
        extra = 1
    else:
        extra = 0
    return wasm_byte_vec_t(len(s) + extra, buf)
