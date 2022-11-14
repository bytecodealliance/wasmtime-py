from . import _ffi as ffi
from ctypes import byref, c_uint64, cast, c_void_p, CFUNCTYPE
import ctypes
from wasmtime import Engine, WasmtimeError
from . import _value as value
import typing

if typing.TYPE_CHECKING:
    from ._wasi import WasiConfig


class Store:
    _ptr: "ctypes._Pointer[ffi.wasmtime_store_t]"
    _context: "ctypes._Pointer[ffi.wasmtime_context_t]"

    def __init__(self, engine: typing.Optional[Engine] = None, data: typing.Optional[typing.Any] = None):

        if engine is None:
            engine = Engine()
        elif not isinstance(engine, Engine):
            raise TypeError("expected an Engine")
        data_id = ffi.c_void_p(0)
        finalize = cast(0, CFUNCTYPE(None, c_void_p))
        if data:
            data_id = value._intern(data)
            finalize = value._externref_finalizer
        self._ptr = ffi.wasmtime_store_new(engine._ptr, data_id, finalize)
        self._context = ffi.wasmtime_store_context(self._ptr)
        self.engine = engine

    def data(self) -> typing.Optional[typing.Any]:
        """
        TODO
        """
        data = ffi.wasmtime_context_get_data(self._context)
        if data:
            return value._unintern(data)
        else:
            return None

    def gc(self) -> None:
        """
        Runs a GC over `externref` values that have been passed into this Store,
        cleaning out anything that is no longer referenced.

        This is not required to be run manually, but can be done so if you'd
        like more precise control over when unreferenced `externref` values are
        deallocated.
        """
        ffi.wasmtime_context_gc(self._context)

    def add_fuel(self, fuel: int) -> None:
        """
        Adds the specified amount of fuel into this store.

        This is only relevant when `Config.consume_fuel` is configured.

        This is a required call to ensure that the store has fuel to
        execute WebAssembly since otherwise stores start with zero fuel.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel.
        """
        err = ffi.wasmtime_context_add_fuel(self._context, fuel)
        if err:
            raise WasmtimeError._from_ptr(err)

    def fuel_consumed(self) -> int:
        """
        Returns the amount of fuel consumed by this `Store` so far.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel.
        """
        fuel = c_uint64(0)
        ok = ffi.wasmtime_context_fuel_consumed(self._context, byref(fuel))
        if ok:
            return fuel.value
        raise WasmtimeError("fuel is not enabled in this store's configuration")

    def consume_fuel(self, fuel: int) -> int:
        """
        Consumes the specified amount of fuel from this store.

        This is only relevant when `Config.consume_fuel` is configured.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel or if the store doesn't have enough fuel remaining.

        Returns the remaining amount of fuel left in the store.
        """
        remaining = c_uint64(0)
        err = ffi.wasmtime_context_consume_fuel(self._context, fuel, byref(remaining))
        if err:
            raise WasmtimeError._from_ptr(err)
        return remaining.value

    def set_wasi(self, wasi: "WasiConfig") -> None:
        """
        TODO
        """
        error = ffi.wasmtime_context_set_wasi(self._context, wasi._ptr)
        delattr(wasi, '_ptr')
        if error:
            raise WasmtimeError._from_ptr(error)

    def set_epoch_deadline(self, ticks_after_current: int) -> None:
        """
        Configures the relative epoch deadline, after the current engine's
        epoch, after which WebAssembly code will trap.
        """
        ffi.wasmtime_context_set_epoch_deadline(self._context, ticks_after_current)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_store_delete(self._ptr)


if typing.TYPE_CHECKING:
    from ._func import Caller


Storelike = typing.Union[Store, "Caller"]
