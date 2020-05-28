__all__ = [
    "Store",
]

from ._engine import Engine
from ._error import WasmtimeError
from ._ffi import dll, P_wasm_store_t, P_wasmtime_interrupt_handle_t

dll.wasm_store_new.restype = P_wasm_store_t
dll.wasmtime_interrupt_handle_new.restype = P_wasmtime_interrupt_handle_t


class Store:
    def __init__(self, engine=None):
        if engine is None:
            engine = Engine()
        elif not isinstance(engine, Engine):
            raise TypeError("expected an Engine")
        self.__ptr__ = dll.wasm_store_new(engine.__ptr__)
        self.engine = engine

    def interrupt_handle(self):
        """
        Creates a new interrupt handle through which execution of wasm can be
        interrupted.

        Raises a `WasmtimeError` if this store's configuration has not been
        configured to enable interruption.

        For more information about this be sure to consult the Rust documentation:
        https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Store.html#method.interrupt_handle
        """

        return InterruptHandle(self)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_store_delete(self.__ptr__)


class InterruptHandle:
    """
    A handle which can be used to interrupt executing WebAssembly code, forcing
    it to trap.

    For more information about this be sure to consult the Rust documentation:
    https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Store.html#method.interrupt_handle
    """

    def __init__(self, store):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        ptr = dll.wasmtime_interrupt_handle_new(store.__ptr__)
        if not ptr:
            raise WasmtimeError("interrupts not enabled on Store")
        self.__ptr__ = ptr

    def interrupt(self):
        """
        Schedules an interrupt to be sent to interrupt this handle's store's
        next (or current) execution of wasm code.
        """
        dll.wasmtime_interrupt_handle_interrupt(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasmtime_interrupt_handle_delete(self.__ptr__)
