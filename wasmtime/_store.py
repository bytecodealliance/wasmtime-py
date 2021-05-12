from . import _ffi as ffi
from ctypes import pointer, byref, c_uint64, cast, c_void_p, CFUNCTYPE
from wasmtime import Engine, WasmtimeError
from . import _value as value
import typing

if typing.TYPE_CHECKING:
    from ._wasi import WasiConfig


class Store:
    _ptr: "pointer[ffi.wasmtime_store_t]"
    _context: "pointer[ffi.wasmtime_context_t]"

    def __init__(self, engine: Engine = None, data: typing.Optional[typing.Any] = None):

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

    def interrupt_handle(self) -> "InterruptHandle":
        """
        Creates a new interrupt handle through which execution of wasm can be
        interrupted.

        Raises a `WasmtimeError` if this store's configuration has not been
        configured to enable interruption.

        For more information about this be sure to consult the Rust documentation:
        https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Store.html#method.interrupt_handle
        """

        return InterruptHandle(self)

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

    def set_wasi(self, wasi: "WasiConfig") -> None:
        """
        TODO
        """
        error = ffi.wasmtime_context_set_wasi(self._context, wasi._ptr)
        delattr(wasi, '_ptr')
        if error:
            raise WasmtimeError._from_ptr(error)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_store_delete(self._ptr)


class InterruptHandle:
    """
    A handle which can be used to interrupt executing WebAssembly code, forcing
    it to trap.

    For more information about this be sure to consult the Rust documentation:
    https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Store.html#method.interrupt_handle
    """

    def __init__(self, store: Store):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        ptr = ffi.wasmtime_interrupt_handle_new(store._context)
        if not ptr:
            raise WasmtimeError("interrupts not enabled on Store")
        self._ptr = ptr

    def interrupt(self) -> None:
        """
        Schedules an interrupt to be sent to interrupt this handle's store's
        next (or current) execution of wasm code.
        """
        ffi.wasmtime_interrupt_handle_interrupt(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_interrupt_handle_delete(self._ptr)


if typing.TYPE_CHECKING:
    from ._func import Caller


Storelike = typing.Union[Store, "Caller"]
