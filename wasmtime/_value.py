from ._error import WasmtimeError
from ._ffi import *
from wasmtime import ValType
import ctypes
import threading
import typing


@ctypes.CFUNCTYPE(None, c_void_p)
def _externref_finalizer(extern_id: int) -> None:
    with Val._pinned_refs_lock:
        Val._id_to_ref_count[extern_id] -= 1
        if Val._id_to_ref_count[extern_id] == 0:
            del Val._id_to_ref_count[extern_id]
            del Val._id_to_extern[extern_id]


class Val:
    # We can't let the extern values we wrap `externref`s around be GC'd, so we
    # pin them in `_id_to_extern`. Additionally, we might make multiple
    # `externref`s to the same extern value, so we count how many references
    # we've created in `_id_to_ref_count`, and only remove a value's entry from
    # `_id_to_extern` once the ref count is zero. Finally, we protect both of
    # these maps with a mutex because `externref`s can be created from any
    # thread.
    _pinned_refs_lock = threading.Lock()
    _id_to_extern: typing.Dict[int, typing.Any] = {}
    _id_to_ref_count: typing.Dict[int, int] = {}

    _raw: typing.Optional[wasm_val_t]

    @classmethod
    def i32(cls, val: int) -> "Val":
        """
        Create a new 32-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I32)
        ffi.of.i32 = val
        return Val(ffi)

    @classmethod
    def i64(cls, val: int) -> "Val":
        """
        Create a new 64-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasm_val_t(WASM_I64)
        ffi.of.i64 = val
        return Val(ffi)

    @classmethod
    def f32(cls, val: float) -> "Val":
        """
        Create a new 32-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F32)
        ffi.of.f32 = val
        return Val(ffi)

    @classmethod
    def f64(cls, val: float) -> "Val":
        """
        Create a new 64-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasm_val_t(WASM_F64)
        ffi.of.f64 = val
        return Val(ffi)

    @classmethod
    def externref(cls, extern: typing.Optional[typing.Any]) -> "Val":
        ffi = wasm_val_t(WASM_ANYREF)
        ffi.of.ref = None

        extern_id = id(extern)
        with Val._pinned_refs_lock:
            Val._id_to_ref_count.setdefault(extern_id, 0)
            Val._id_to_ref_count[extern_id] += 1
            Val._id_to_extern[extern_id] = extern
        wasmtime_externref_new_with_finalizer(ctypes.c_void_p(extern_id),
                                              _externref_finalizer,
                                              ctypes.byref(ffi))
        return Val(ffi)

    @classmethod
    def funcref(cls, f: "typing.Optional[wasmtime.Func]") -> "Val":
        ffi = wasm_val_t(WASM_FUNCREF)
        ffi.of.ref = None
        if f is None:
            return Val(ffi)

        if not isinstance(f, wasmtime.Func):
            raise TypeError("Expected a Func or None")

        wasmtime_func_as_funcref(f._ptr, ctypes.byref(ffi))
        return Val(ffi)

    @classmethod
    def ref_null(cls, ty: ValType) -> "Val":
        """
        Create a null reference value of the given type.

        Raise an exception if `ty` is not a reference type.
        """
        if ty == ValType.externref():
            return Val.externref(None)
        if ty == ValType.funcref():
            return Val.funcref(None)
        raise WasmtimeError("Invalid reference type for `ref_null`: %s" % ty)

    def __init__(self, raw: wasm_val_t):
        if not isinstance(raw, wasm_val_t):
            raise TypeError("expected a raw value")
        self._raw = raw

    def __eq__(self, rhs: typing.Any) -> typing.Any:
        if isinstance(rhs, Val):
            return self._unwrap_raw().kind == rhs._unwrap_raw().kind and self.value == rhs.value
        return self.value == rhs

    def __del__(self) -> None:
        if hasattr(self, "_raw") and self._raw is not None:
            wasm_val_delete(ctypes.byref(self._raw))

    def _clone(self) -> "Val":
        raw = self._unwrap_raw()
        clone = wasm_val_t(WASM_I32)
        wasm_val_copy(ctypes.byref(clone), byref(raw))
        return Val(clone)

    @classmethod
    def _convert(cls, ty: ValType, val: "IntoVal") -> "Val":
        if isinstance(val, Val):
            if ty != val.type:
                raise TypeError("wrong type of `Val` provided")
            return val
        elif isinstance(val, int):
            if ty == ValType.i32():
                return Val.i32(val)
            if ty == ValType.i64():
                return Val.i64(val)
        elif isinstance(val, float):
            if ty == ValType.f32():
                return Val.f32(val)
            if ty == ValType.f64():
                return Val.f64(val)
        elif isinstance(val, wasmtime.Func):
            return Val.funcref(val)
        elif val is None:
            if ty == ValType.externref():
                return Val.externref(None)
            if ty == ValType.funcref():
                return Val.funcref(None)
        elif ty == ValType.externref():
            return Val.externref(val)
        raise TypeError("don't know how to convert %r to %s" % (val, ty))

    def _into_raw(self) -> wasm_val_t:
        raw = self._unwrap_raw()
        self._raw = None
        return raw

    def _unwrap_raw(self) -> wasm_val_t:
        if isinstance(self._raw, wasm_val_t):
            return self._raw
        else:
            raise WasmtimeError("use of moved `Val`")

    @classmethod
    def _value(cls, raw: wasm_val_t) -> typing.Union[int, float, "wasmtime.Func", typing.Any]:
        if raw.kind == WASM_I32.value:
            return raw.of.i32
        if raw.kind == WASM_I64.value:
            return raw.of.i64
        if raw.kind == WASM_F32.value:
            return raw.of.f32
        if raw.kind == WASM_F64.value:
            return raw.of.f64
        if raw.kind == WASM_ANYREF.value:
            return Val._as_externref(raw)
        if raw.kind == WASM_FUNCREF.value:
            return Val._as_funcref(raw)
        raise WasmtimeError("Unkown `wasm_valkind_t`: {}".format(raw.kind))

    @property
    def value(self) -> typing.Union[int, float, "wasmtime.Func", typing.Any]:
        """
        Get the the underlying value as a python value

        Returns `None` if the value can't be represented in Python, or if the
        value is a null reference type.
        """
        return Val._value(self._unwrap_raw())

    def as_i32(self) -> typing.Optional[int]:
        """
        Get the 32-bit integer value of this value, or `None` if it's not an i32
        """
        raw = self._unwrap_raw()
        if raw.kind == WASM_I32.value:
            return raw.of.i32
        else:
            return None

    def as_i64(self) -> typing.Optional[int]:
        """
        Get the 64-bit integer value of this value, or `None` if it's not an i64
        """
        raw = self._unwrap_raw()
        if raw.kind == WASM_I64.value:
            return raw.of.i64
        else:
            return None

    def as_f32(self) -> typing.Optional[float]:
        """
        Get the 32-bit float value of this value, or `None` if it's not an f32
        """
        raw = self._unwrap_raw()
        if raw.kind == WASM_F32.value:
            return raw.of.f32
        else:
            return None

    def as_f64(self) -> typing.Optional[float]:
        """
        Get the 64-bit float value of this value, or `None` if it's not an f64
        """
        raw = self._unwrap_raw()
        if raw.kind == WASM_F64.value:
            return raw.of.f64
        else:
            return None

    @classmethod
    def _as_externref(cls, raw: wasm_val_t) -> typing.Optional[typing.Any]:
        if raw.kind != WASM_ANYREF.value:
            return None
        extern_id = ctypes.c_void_p(0)
        wasmtime_externref_data(ctypes.byref(raw), ctypes.byref(extern_id))
        if extern_id.value is None:
            return None
        with Val._pinned_refs_lock:
            return Val._id_to_extern.get(extern_id.value)

    def as_externref(self) -> typing.Optional[typing.Any]:
        """
        Get the extern data referenced by this `externref` value, or `None` if
        it's not an `externref`.
        """
        return Val._as_externref(self._unwrap_raw())

    @classmethod
    def _as_funcref(cls, raw: wasm_val_t) -> typing.Optional["wasmtime.Func"]:
        if raw.kind != WASM_FUNCREF.value:
            return None
        ptr = wasmtime_funcref_as_func(ctypes.byref(raw))
        if ptr:
            return wasmtime.Func._from_ptr(ptr, None)
        else:
            return None

    def as_funcref(self) -> typing.Optional["wasmtime.Func"]:
        """
        Get the function that this `funcref` value is referencing, or `None` if
        this is not a `funcref` value, or is a null reference.
        """
        return Val._as_funcref(self._unwrap_raw())

    @property
    def type(self) -> ValType:
        """
        Returns the `ValType` corresponding to this `Val`
        """
        ptr = dll.wasm_valtype_new(self._unwrap_raw().kind)
        return ValType._from_ptr(ptr, None)


IntoVal = typing.Union[
    # Id.
    Val,

    # `i32` and `i64`
    int,

    # `f32` and `f64`
    float,

    # Null reference types
    None,

    # `funcref`
    "wasmtime.Func",

    # `externref`
    typing.Any
]


# This needs to be imported so that mypy understands `wasmtime.Func` in typings,
# but it also has to come after `Val`'s definition to deal with circular module
# dependency issues.
import wasmtime  # noqa: E402
