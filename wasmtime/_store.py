from . import _ffi as ffi
from ctypes import byref, c_uint64, cast, c_void_p, CFUNCTYPE
import ctypes
from wasmtime import Engine, WasmtimeError, Managed
from . import _value as value
import typing

if typing.TYPE_CHECKING:
    from ._wasi import WasiConfig


class Store(Managed["ctypes._Pointer[ffi.wasmtime_store_t]"]):
    __context: "typing.Optional[ctypes._Pointer[ffi.wasmtime_context_t]]"

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
        self._set_ptr(ffi.wasmtime_store_new(engine.ptr(), data_id, finalize))
        self.__context = ffi.wasmtime_store_context(self.ptr())
        self.engine = engine

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_store_t]") -> None:
        ffi.wasmtime_store_delete(ptr)
        self.__context = None

    def _context(self) -> "ctypes._Pointer[ffi.wasmtime_context_t]":
        if self.__context is None:
            raise ValueError('already closed')
        return self.__context

    def data(self) -> typing.Optional[typing.Any]:
        """
        TODO
        """
        data = ffi.wasmtime_context_get_data(self._context())
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
        ffi.wasmtime_context_gc(self._context())

    def set_fuel(self, fuel: int) -> None:
        """
        Sets the amount of fuel in this store to `fuel`.

        This is only relevant when `Config.consume_fuel` is configured.

        This is a required call to ensure that the store has fuel to
        execute WebAssembly since otherwise stores start with zero fuel.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel.
        """
        err = ffi.wasmtime_context_set_fuel(self._context(), fuel)
        if err:
            raise WasmtimeError._from_ptr(err)

    def get_fuel(self) -> int:
        """
        Returns the amount of fuel left in the store.

        This is only relevant when `Config.consume_fuel` is configured.

        Raises a `WasmtimeError` if this store's configuration is not configured
        to consume fuel or if the store doesn't have enough fuel remaining.
        """
        remaining = c_uint64(0)
        err = ffi.wasmtime_context_get_fuel(self._context(), byref(remaining))
        if err:
            raise WasmtimeError._from_ptr(err)
        return remaining.value

    def set_wasi(self, wasi: "WasiConfig") -> None:
        """
        TODO
        """
        error = ffi.wasmtime_context_set_wasi(self._context(), wasi._consume())
        if error:
            raise WasmtimeError._from_ptr(error)

    def set_epoch_deadline(self, ticks_after_current: int) -> None:
        """
        Configures the relative epoch deadline, after the current engine's
        epoch, after which WebAssembly code will trap.
        """
        ffi.wasmtime_context_set_epoch_deadline(self._context(), ticks_after_current)

    def set_limits(self,
                   memory_size: int = -1,
                   table_elements: int = -1,
                   instances: int = -1,
                   tables: int = -1,
                   memories: int = -1) -> None:
        """
        Configures the limits of various items within this store.

        * `memory_size` - the maximum size, in bytes, that linear memory is
          allowed to consume within this store. Setting this to a lower value
          will cause instantiation to fail if a module needs more memory.
          Additionally the `memory.grow` instruction will return -1 once this
          threshold is reached.

        * `table_elements` - the maximum number of elements that can be stored
          within tables in this store. Currently each table element takes 8
          bytes.

        * `instances` - the maximum number of WebAssembly instances that can
          be created.

        * `tables` - the maximum number of WebAssembly tables that can
          be created.

        * `memories` - the maximum number of WebAssembly linear memories that
          can be created.

        If any limit is negative then the limit will not be set as a part of
        this invocation and it will be ignored.
        """
        ffi.wasmtime_store_limiter(self.ptr(), memory_size, table_elements, instances, tables, memories)


if typing.TYPE_CHECKING:
    from ._func import Caller


Storelike = typing.Union[Store, "Caller"]
