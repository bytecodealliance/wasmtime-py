from . import _ffi as ffi
from ctypes import *
from wasmtime import GlobalType, Val, WasmtimeError, IntoVal
from ._store import Storelike


class Global:
    _global: ffi.wasmtime_global_t

    def __init__(self, store: Storelike, ty: GlobalType, val: IntoVal):
        if not isinstance(ty, GlobalType):
            raise TypeError("expected a GlobalType")
        val = Val._convert(ty.content, val)
        global_ = ffi.wasmtime_global_t()
        error = ffi.wasmtime_global_new(
            store._context,
            ty._ptr,
            byref(val._unwrap_raw()),
            byref(global_))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._global = global_

    @classmethod
    def _from_raw(cls, global_: ffi.wasmtime_global_t) -> "Global":
        ty: "Global" = cls.__new__(cls)
        ty._global = global_
        return ty

    def type(self, store: Storelike) -> GlobalType:
        """
        Gets the type of this global as a `GlobalType`
        """

        ptr = ffi.wasmtime_global_type(store._context, byref(self._global))
        return GlobalType._from_ptr(ptr, None)

    def value(self, store: Storelike) -> IntoVal:
        """
        Gets the current value of this global

        Returns a native python type
        """
        raw = ffi.wasmtime_val_t()
        ffi.wasmtime_global_get(store._context, byref(self._global), byref(raw))
        val = Val(raw)
        if val.value is not None:
            return val.value
        else:
            return val

    def set_value(self, store: Storelike, val: IntoVal) -> None:
        """
        Sets the value of this global to a new value
        """
        val = Val._convert(self.type(store).content, val)
        error = ffi.wasmtime_global_set(store._context, byref(self._global), byref(val._unwrap_raw()))
        if error:
            raise WasmtimeError._from_ptr(error)

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(global_=self._global)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_GLOBAL, union)
