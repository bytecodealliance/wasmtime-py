from ._error import WasmtimeError
from ._types import ValType
import ctypes
import typing
from ._slab import Slab

from . import _ffi as ffi

if typing.TYPE_CHECKING:
    from ._store import Storelike


SLAB: Slab[typing.Any] = Slab()


# Note that 0 as a `c_void_p` is reserved for null-lookalike externrefs so
# indices from the slabs are off-by-one.
@ctypes.CFUNCTYPE(None, ctypes.c_void_p)
def _externref_finalizer(idx: int) -> None:
    SLAB.deallocate(idx - 1)


def _intern(obj: typing.Any) -> int:
    return SLAB.allocate(obj) + 1


def _unintern(idx: int) -> typing.Any:
    return SLAB.get(idx - 1)


class Val:
    _kind: ffi.wasmtime_valkind_t
    _val: typing.Any

    @classmethod
    def i32(cls, val: int) -> "Val":
        """
        Create a new 32-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        val = ffi.wasmtime_valunion_t(i32=val).i32
        return Val(ffi.WASMTIME_I32, val)

    @classmethod
    def i64(cls, val: int) -> "Val":
        """
        Create a new 64-bit integer value
        """
        if not isinstance(val, int):
            raise TypeError("expected an integer")
        val = ffi.wasmtime_valunion_t(i64=val).i64
        return Val(ffi.WASMTIME_I64, val)

    @classmethod
    def f32(cls, val: float) -> "Val":
        """
        Create a new 32-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        val = ffi.wasmtime_valunion_t(f32=val).f32
        return Val(ffi.WASMTIME_F32, val)

    @classmethod
    def f64(cls, val: float) -> "Val":
        """
        Create a new 64-bit float value
        """
        if not isinstance(val, float):
            raise TypeError("expected a float")
        val = ffi.wasmtime_valunion_t(f64=val).f64
        return Val(ffi.WASMTIME_F64, val)

    @classmethod
    def externref(cls, extern: typing.Optional[typing.Any]) -> "Val":
        return Val(ffi.WASMTIME_EXTERNREF, extern)

    @classmethod
    def funcref(cls, f: "typing.Optional[wasmtime.Func]") -> "Val":
        return Val(ffi.WASMTIME_FUNCREF, f)

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

    def __init__(self, kind: ffi.wasmtime_valkind_t, val: typing.Any):
        self._kind = kind
        self._val = val

    def __eq__(self, rhs: typing.Any) -> typing.Any:
        if isinstance(rhs, Val):
            return self._kind == rhs._kind and self._val == rhs._val
        return self._val == rhs

    @classmethod
    def _convert_to_raw(cls, store: 'Storelike', ty: ValType, val: typing.Any) -> ffi.wasmtime_val_t:
        if isinstance(val, Val):
            if ty != val.type:
                raise TypeError("wrong type of `Val` provided")
            return val._new_raw(store)
        if ty == ValType.externref():
            return Val.externref(val)._new_raw(store)
        elif isinstance(val, int):
            if ty == ValType.i32():
                return Val.i32(val)._new_raw(store)
            if ty == ValType.i64():
                return Val.i64(val)._new_raw(store)
        elif isinstance(val, float):
            if ty == ValType.f32():
                return Val.f32(val)._new_raw(store)
            if ty == ValType.f64():
                return Val.f64(val)._new_raw(store)
        elif isinstance(val, wasmtime.Func):
            return Val.funcref(val)._new_raw(store)
        elif val is None:
            if ty == ValType.externref():
                return Val.externref(None)._new_raw(store)
            if ty == ValType.funcref():
                return Val.funcref(None)._new_raw(store)
        raise TypeError("don't know how to convert %r to %s" % (val, ty))

    def _new_raw(self, store: 'Storelike') -> ffi.wasmtime_val_t:
        ret = ffi.wasmtime_val_t(kind = self._kind)
        if ret.kind == ffi.WASMTIME_I32.value:
            ret.of.i32 = self._val
        elif ret.kind == ffi.WASMTIME_I64.value:
            ret.of.i64 = self._val
        elif ret.kind == ffi.WASMTIME_F32.value:
            ret.of.f32 = self._val
        elif ret.kind == ffi.WASMTIME_F64.value:
            ret.of.f64 = self._val
        elif ret.kind == ffi.WASMTIME_EXTERNREF.value:
            if self._val is not None:
                extern_id = _intern(self._val)
                if not ffi.wasmtime_externref_new(store._context(), extern_id, _externref_finalizer,
                                              ctypes.byref(ret.of.externref)):
                    raise WasmtimeError("failed to create an externref value")
            else:

                ret.of.externref.store_id = 0
        elif ret.kind == ffi.WASMTIME_FUNCREF.value:
            if self._val is not None:
                ret.of.funcref = self._val._func
        else:
            raise RuntimeError("unknown kind")
        return ret

    @classmethod
    def _from_raw(cls, store: 'Storelike', raw: ffi.wasmtime_val_t, owned: bool = True) -> 'Val':
        val: typing.Any = None
        if raw.kind == ffi.WASMTIME_I32.value:
            val = raw.of.i32
        elif raw.kind == ffi.WASMTIME_I64.value:
            val = raw.of.i64
        elif raw.kind == ffi.WASMTIME_F32.value:
            val = raw.of.f32
        elif raw.kind == ffi.WASMTIME_F64.value:
            val = raw.of.f64
        elif raw.kind == ffi.WASMTIME_EXTERNREF.value:
            if raw.of.externref:
                extern_id = ffi.wasmtime_externref_data(store._context(), raw.of.externref)
                # FIXME https://github.com/bytecodealliance/wasmtime-py/issues/303
                if extern_id:
                    val = _unintern(extern_id)  # type: ignore
        elif raw.kind == ffi.WASMTIME_FUNCREF.value:
            if raw.of.funcref.store_id != 0:
                val = wasmtime.Func._from_raw(raw.of.funcref)
        else:
            raise WasmtimeError("Unkown `ffi.wasmtime_valkind_t`: {}".format(raw.kind))

        if owned:
            ffi.wasmtime_val_unroot(ctypes.byref(raw))

        return Val(raw.kind, val)

    @property
    def value(self) -> typing.Any:
        """
        Get the the underlying value as a python value
        """
        return self._val

    def as_i32(self) -> typing.Optional[int]:
        """
        Get the 32-bit integer value of this value, or `None` if it's not an i32
        """
        if self._kind == ffi.WASMTIME_I32:
            assert(isinstance(self._val, int))
            return self._val
        else:
            return None

    def as_i64(self) -> typing.Optional[int]:
        """
        Get the 64-bit integer value of this value, or `None` if it's not an i64
        """
        if self._kind == ffi.WASMTIME_I64:
            assert(isinstance(self._val, int))
            return self._val
        else:
            return None

    def as_f32(self) -> typing.Optional[float]:
        """
        Get the 32-bit float value of this value, or `None` if it's not an f32
        """
        if self._kind == ffi.WASMTIME_F32:
            assert(isinstance(self._val, float))
            return self._val
        else:
            return None

    def as_f64(self) -> typing.Optional[float]:
        """
        Get the 64-bit float value of this value, or `None` if it's not an f64
        """
        if self._kind == ffi.WASMTIME_F64:
            assert(isinstance(self._val, float))
            return self._val
        else:
            return None

    def as_externref(self) -> typing.Optional[typing.Any]:
        """
        Get the extern data referenced by this `externref` value, or `None` if
        it's not an `externref`.
        """
        if self._kind == ffi.WASMTIME_EXTERNREF:
            return self._val
        else:
            return None

    def as_funcref(self) -> typing.Optional["wasmtime.Func"]:
        """
        Get the function that this `funcref` value is referencing, or `None` if
        this is not a `funcref` value, or is a null reference.
        """
        if self._kind == ffi.WASMTIME_FUNCREF:
            assert(isinstance(self._val, wasmtime.Func))
            return self._val
        else:
            return None

    @property
    def type(self) -> ValType:
        """
        Returns the `ValType` corresponding to this `Val`
        """
        kind = self._kind
        if kind == ffi.WASMTIME_I32:
            return ValType.i32()
        elif kind == ffi.WASMTIME_I64:
            return ValType.i64()
        elif kind == ffi.WASMTIME_F32:
            return ValType.f32()
        elif kind == ffi.WASMTIME_F64:
            return ValType.f64()
        elif kind == ffi.WASMTIME_V128:
            raise Exception("unimplemented v128 type")
        elif kind == ffi.WASMTIME_EXTERNREF:
            return ValType.externref()
        elif kind == ffi.WASMTIME_FUNCREF:
            return ValType.funcref()
        else:
            raise Exception("unknown kind %d" % kind.value)


# This needs to be imported so that mypy understands `wasmtime.Func` in typings,
# but it also has to come after `Val`'s definition to deal with circular module
# dependency issues.
import wasmtime  # noqa: E402
