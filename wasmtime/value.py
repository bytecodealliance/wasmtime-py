from .ffi import *
from ctypes import *

class Val:
    # Create a new 32-bit integer value
    @classmethod
    def i32(cls, val):
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I32)
        ffi.of.i32 = val
        return Val(ffi)

    # Create a new 64-bit integer value
    @classmethod
    def i64(cls, val):
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I64)
        ffi.of.i64 = val
        return Val(ffi)

    # Create a new 32-bit float value
    @classmethod
    def f32(cls, val):
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F32)
        ffi.of.f32 = val
        return Val(ffi)

    # Create a new 64-bit float value
    @classmethod
    def f64(cls, val):
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F64)
        ffi.of.f64 = val
        return Val(ffi)

    def __init__(self, raw):
        if not isinstance(raw, wasm_val_t):
            raise TypeError("expected a raw value")
        self.__raw__ = raw

    # Get the 32-bit integer value of this value, or `None` if it's not an i32
    def get_i32(self):
        if self.__raw__.kind == WASM_I32.value:
            return self.__raw__.of.i32
        else:
            return None

    # Get the 64-bit integer value of this value, or `None` if it's not an i64
    def get_i64(self):
        if self.__raw__.kind == WASM_I64.value:
            return self.__raw__.of.i64
        else:
            return None

    # Get the 32-bit float value of this value, or `None` if it's not an f32
    def get_f32(self):
        if self.__raw__.kind == WASM_F32.value:
            return self.__raw__.of.f32
        else:
            return None

    # Get the 64-bit float value of this value, or `None` if it's not an f64
    def get_f64(self):
        if self.__raw__.kind == WASM_F64.value:
            return self.__raw__.of.f64
        else:
            return None
