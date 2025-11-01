import ctypes

from . import _bindings
from . import _ffi as ffi
from wasmtime import GlobalType, Val, WasmtimeError
from typing import Any
from ._store import Storelike


class Global:
    _global: _bindings.wasmtime_global_t

    def __init__(self, store: Storelike, ty: GlobalType, val: Any):
        if not isinstance(ty, GlobalType):
            raise TypeError("expected a GlobalType")
        val = Val._convert_to_raw(store, ty.content, val)
        global_ = _bindings.wasmtime_global_t()
        error = _bindings.wasmtime_global_new(
            store._context(),
            ty.ptr(),
            ctypes.byref(val),
            ctypes.byref(global_))
        _bindings.wasmtime_val_unroot(ctypes.byref(val))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._global = global_

    @classmethod
    def _from_raw(cls, global_: _bindings.wasmtime_global_t) -> "Global":
        ty: "Global" = cls.__new__(cls)
        ty._global = global_
        return ty

    def type(self, store: Storelike) -> GlobalType:
        """
        Gets the type of this global as a `GlobalType`
        """

        ptr = _bindings.wasmtime_global_type(store._context(), ctypes.byref(self._global))
        return GlobalType._from_ptr(ptr, None)

    def value(self, store: Storelike) -> Any:
        """
        Gets the current value of this global

        Returns a native python type
        """
        raw = _bindings.wasmtime_val_t()
        _bindings.wasmtime_global_get(store._context(), ctypes.byref(self._global), ctypes.byref(raw))
        val = Val._from_raw(store, raw)
        if val.value is not None:
            return val.value
        else:
            return val

    def set_value(self, store: Storelike, val: Any) -> None:
        """
        Sets the value of this global to a new value
        """
        val = Val._convert_to_raw(store, self.type(store).content, val)
        error = _bindings.wasmtime_global_set(store._context(), ctypes.byref(self._global), ctypes.byref(val))
        _bindings.wasmtime_val_unroot(ctypes.byref(val))
        if error:
            raise WasmtimeError._from_ptr(error)

    def _as_extern(self) -> _bindings.wasmtime_extern_t:
        union = _bindings.wasmtime_extern_union(global_=self._global)
        return _bindings.wasmtime_extern_t(ffi.WASMTIME_EXTERN_GLOBAL, union)
