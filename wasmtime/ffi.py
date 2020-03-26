from ctypes import *
import os

if sys.maxsize <= 2**32:
    raise RuntimeError("wasmtime only works on 64-bit platforms right now")

filename = os.path.join(os.path.dirname(__file__), 'wasmtime.pyd')
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


class wasm_val_union(Union):
    _fields_ = [
        ("i32", c_int32),
        ("i64", c_int64),
        ("f32", c_float),
        ("f64", c_double),
    ]


class wasm_val_t(Structure):
    _fields_ = [("kind", c_uint8), ("of", wasm_val_union)]
