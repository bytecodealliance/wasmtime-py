from ._ffi import *
from wasmtime import ValType


class Val:
    @classmethod
    def i32(cls, val):
        """
        Create a new 32-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I32)
        ffi.of.i32 = val
        return Val(ffi)

    @classmethod
    def i64(cls, val):
        """
        Create a new 64-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I64)
        ffi.of.i64 = val
        return Val(ffi)

    @classmethod
    def f32(cls, val):
        """
        Create a new 32-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F32)
        ffi.of.f32 = val
        return Val(ffi)

    @classmethod
    def f64(cls, val):
        """
        Create a new 64-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F64)
        ffi.of.f64 = val
        return Val(ffi)

    def __init__(self, raw):
        if not isinstance(raw, wasm_val_t):
            raise TypeError("expected a raw value")
        self.__raw__ = raw

    @classmethod
    def __convert__(cls, ty, val):
        if isinstance(val, Val):
            if ty != val.type:
                raise TypeError("wrong type of `Val` provided")
            return val
        if ty == ValType.i32():
            return Val.i32(val)
        if ty == ValType.i64():
            return Val.i64(val)
        if ty == ValType.f32():
            return Val.f32(val)
        if ty == ValType.f64():
            return Val.f64(val)
        raise WasmtimeError("don't know how to convert %r to %s" % (val, ty))

    @property
    def value(self):
        """
        Get the the underlying value as a python value

        Returns `None` if the value can't be represented in Python
        """
        if self.__raw__.kind == WASM_I32.value:
            return self.__raw__.of.i32
        if self.__raw__.kind == WASM_I64.value:
            return self.__raw__.of.i64
        if self.__raw__.kind == WASM_F32.value:
            return self.__raw__.of.f32
        if self.__raw__.kind == WASM_F64.value:
            return self.__raw__.of.f64
        return None

    def as_i32(self):
        """
        Get the 32-bit integer value of this value, or `None` if it's not an i32
        """
        if self.__raw__.kind == WASM_I32.value:
            return self.__raw__.of.i32
        else:
            return None

    def as_i64(self):
        """
        Get the 64-bit integer value of this value, or `None` if it's not an i64
        """
        if self.__raw__.kind == WASM_I64.value:
            return self.__raw__.of.i64
        else:
            return None

    def as_f32(self):
        """
        Get the 32-bit float value of this value, or `None` if it's not an f32
        """
        if self.__raw__.kind == WASM_F32.value:
            return self.__raw__.of.f32
        else:
            return None

    def as_f64(self):
        """
        Get the 64-bit float value of this value, or `None` if it's not an f64
        """
        if self.__raw__.kind == WASM_F64.value:
            return self.__raw__.of.f64
        else:
            return None

    @property
    def type(self):
        """
        Returns the `ValType` corresponding to this `Val`
        """
        ptr = dll.wasm_valtype_new(self.__raw__.kind)
        return ValType.__from_ptr__(ptr, None)
