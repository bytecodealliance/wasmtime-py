from . import _ffi as ffi
from ctypes import *
from wasmtime import Store, GlobalType, Val, WasmtimeError, IntoVal
from typing import Optional, Any


class Global:
    def __init__(self, store: Store, ty: GlobalType, val: IntoVal):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, GlobalType):
            raise TypeError("expected a GlobalType")
        val = Val.__convert__(ty.content, val)
        ptr = POINTER(ffi.wasm_global_t)()
        error = ffi.wasmtime_global_new(
            store._ptr,
            ty._ptr,
            byref(val._raw),
            byref(ptr))
        if error:
            raise WasmtimeError.__from_ptr__(error)
        self._ptr = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr: "pointer[ffi.wasm_global_t]", owner: Optional[Any]) -> "Global":
        ty: "Global" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_global_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty.__owner__ = owner
        return ty

    @property
    def type(self) -> GlobalType:
        """
        Gets the type of this global as a `GlobalType`
        """

        ptr = ffi.wasm_global_type(self._ptr)
        return GlobalType.__from_ptr__(ptr, None)

    @property
    def value(self) -> IntoVal:
        """
        Gets the current value of this global

        Returns a native python type
        """
        raw = ffi.wasm_val_t()
        ffi.wasm_global_get(self._ptr, byref(raw))
        val = Val(raw)
        if val.value:
            return val.value
        else:
            return val

    @value.setter
    def value(self, val: IntoVal) -> None:
        """
        Sets the value of this global to a new value
        """
        val = Val.__convert__(self.type.content, val)
        error = ffi.wasmtime_global_set(self._ptr, byref(val._raw))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_global_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_global_delete(self._ptr)
