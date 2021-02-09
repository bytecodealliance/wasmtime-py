from . import _ffi as ffi
from ctypes import pointer, byref, c_ulonglong
from wasmtime import Engine, WasmtimeError


class Store:
    _ptr: "pointer[ffi.wasm_store_t]"

    def __init__(self, engine: Engine = None):
        if engine is None:
            engine = Engine()
        elif not isinstance(engine, Engine):
            raise TypeError("expected an Engine")
        self._ptr = ffi.wasm_store_new(engine._ptr)
        self.engine = engine

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
        ffi.wasmtime_store_gc(self._ptr)

    def add_fuel(self, fuel: int) -> None:
        """
        Adds the specified amount of fuel into this store.

        This is only relevant when `Config.consume_fuel` is configured.

        This is a required call to ensure that the store has fuel to
        execute WebAssembly since otherwise stores start with zero fuel.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel.
        """
        err = ffi.wasmtime_store_add_fuel(self._ptr, fuel)
        if err:
            raise WasmtimeError._from_ptr(err)

    def fuel_consumed(self) -> int:
        """
        Returns the amount of fuel consumed by this `Store` so far.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel.
        """
        fuel = c_ulonglong(0)
        ok = ffi.wasmtime_store_fuel_consumed(self._ptr, byref(fuel))
        if ok:
            return fuel.value
        raise WasmtimeError("fuel is not enabled in this store's configuration")

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasm_store_delete(self._ptr)


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
        ptr = ffi.wasmtime_interrupt_handle_new(store._ptr)
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
