from ._error import WasmtimeError
from ._ffi import *
from ._types import ValType
import ctypes
import typing


@ctypes.CFUNCTYPE(None, c_void_p)
def _externref_finalizer(extern_id: int) -> None:
    Val._id_to_ref_count[extern_id] -= 1
    if Val._id_to_ref_count[extern_id] == 0:
        del Val._id_to_ref_count[extern_id]
        del Val._id_to_extern[extern_id]


def _intern(obj: typing.Any) -> c_void_p:
    extern_id = id(obj)
    Val._id_to_ref_count.setdefault(extern_id, 0)
    Val._id_to_ref_count[extern_id] += 1
    Val._id_to_extern[extern_id] = obj
    return ctypes.c_void_p(extern_id)


def _unintern(val: int) -> typing.Any:
    return Val._id_to_extern.get(val)


class Val:
    # We can't let the extern values we wrap `externref`s around be GC'd, so we
    # pin them in `_id_to_extern`. Additionally, we might make multiple
    # `externref`s to the same extern value, so we count how many references
    # we've created in `_id_to_ref_count`, and only remove a value's entry from
    # `_id_to_extern` once the ref count is zero.
    _id_to_extern: typing.Dict[int, typing.Any] = {}
    _id_to_ref_count: typing.Dict[int, int] = {}

    _raw: typing.Optional[wasmtime_val_t]

    @classmethod
    def i32(cls, val: int) -> "Val":
        """
        Create a new 32-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasmtime_val_t(WASMTIME_I32, wasmtime_valunion(i32=val))
        return Val(ffi)

    @classmethod
    def i64(cls, val: int) -> "Val":
        """
        Create a new 64-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        ffi = wasmtime_val_t(WASMTIME_I64, wasmtime_valunion(i64=val))
        return Val(ffi)

    @classmethod
    def f32(cls, val: float) -> "Val":
        """
        Create a new 32-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasmtime_val_t(WASMTIME_F32, wasmtime_valunion(f32=val))
        return Val(ffi)

    @classmethod
    def f64(cls, val: float) -> "Val":
        """
        Create a new 64-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        ffi = wasmtime_val_t(WASMTIME_F64, wasmtime_valunion(f64=val))
        return Val(ffi)

    @classmethod
    def externref(cls, extern: typing.Optional[typing.Any]) -> "Val":
        ffi = wasmtime_val_t(WASMTIME_EXTERNREF)
        ffi.of.externref = POINTER(wasmtime_externref_t)()
        if extern is not None:
            extern_id = _intern(extern)
            ptr = wasmtime_externref_new(extern_id, _externref_finalizer)
            ffi.of.externref = ptr
        return Val(ffi)

    @classmethod
    def funcref(cls, f: "typing.Optional[wasmtime.Func]") -> "Val":
        ffi = wasmtime_val_t(WASMTIME_FUNCREF)
        if f:
            ffi.of.funcref = f._func
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

    def __init__(self, raw: wasmtime_val_t):
        self._raw = raw

    def __eq__(self, rhs: typing.Any) -> typing.Any:
        if isinstance(rhs, Val):
            return self._unwrap_raw().kind == rhs._unwrap_raw().kind and self.value == rhs.value
        return self.value == rhs

    def __del__(self) -> None:
        if hasattr(self, "_raw") and self._raw is not None:
            wasmtime_val_delete(ctypes.byref(self._raw))

    def _clone(self) -> "Val":
        raw = self._unwrap_raw()
        if raw.kind == WASMTIME_EXTERNREF and raw.of.externref:
            externref = wasmtime_externref_clone(raw.of.externref)
            raw = wasmtime_val_t(WASMTIME_EXTERNREF)
            raw.of.externref = externref
        return Val(raw)

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

    def _into_raw(self) -> wasmtime_val_t:
        raw = self._unwrap_raw()
        self._raw = None
        return raw

    def _unwrap_raw(self) -> wasmtime_val_t:
        if isinstance(self._raw, wasmtime_val_t):
            return self._raw
        else:
            raise WasmtimeError("use of moved `Val`")

    @classmethod
    def _value(cls, raw: wasmtime_val_t) -> typing.Union[int, float, "wasmtime.Func", typing.Any]:
        if raw.kind == WASMTIME_I32.value:
            return raw.of.i32
        if raw.kind == WASMTIME_I64.value:
            return raw.of.i64
        if raw.kind == WASMTIME_F32.value:
            return raw.of.f32
        if raw.kind == WASMTIME_F64.value:
            return raw.of.f64
        if raw.kind == WASMTIME_EXTERNREF.value:
            return Val._as_externref(raw)
        if raw.kind == WASMTIME_FUNCREF.value:
            return Val._as_funcref(raw)
        raise WasmtimeError("Unkown `wasmtime_valkind_t`: {}".format(raw.kind))

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
        if raw.kind == WASMTIME_I32.value:
            return int(raw.of.i32)
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
        if raw.kind == WASMTIME_F32.value:
            return raw.of.f32
        else:
            return None

    def as_f64(self) -> typing.Optional[float]:
        """
        Get the 64-bit float value of this value, or `None` if it's not an f64
        """
        raw = self._unwrap_raw()
        if raw.kind == WASMTIME_F64.value:
            return raw.of.f64
        else:
            return None

    @classmethod
    def _as_externref(cls, raw: wasmtime_val_t) -> typing.Optional[typing.Any]:
        if raw.kind != WASMTIME_EXTERNREF.value:
            return None
        if not raw.of.externref:
            return None
        extern_id = wasmtime_externref_data(raw.of.externref)
        return _unintern(extern_id)

    def as_externref(self) -> typing.Optional[typing.Any]:
        """
        Get the extern data referenced by this `externref` value, or `None` if
        it's not an `externref`.
        """
        return Val._as_externref(self._unwrap_raw())

    @classmethod
    def _as_funcref(cls, raw: wasmtime_val_t) -> typing.Optional["wasmtime.Func"]:
        if raw.kind != WASMTIME_FUNCREF.value:
            return None
        if raw.of.funcref.store_id == 0:
            return None
        else:
            return wasmtime.Func._from_raw(raw.of.funcref)

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
        kind = self._unwrap_raw().kind
        if kind == WASMTIME_I32.value:
            return ValType.i32()
        elif kind == WASMTIME_I64.value:
            return ValType.i64()
        elif kind == WASMTIME_F32.value:
            return ValType.f32()
        elif kind == WASMTIME_F64.value:
            return ValType.f64()
        elif kind == WASMTIME_V128.value:
            raise Exception("unimplemented v128 type")
        elif kind == WASMTIME_EXTERNREF.value:
            return ValType.externref()
        elif kind == WASMTIME_FUNCREF.value:
            return ValType.funcref()
        else:
            raise Exception("unknown kind %d" % kind.value)


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
