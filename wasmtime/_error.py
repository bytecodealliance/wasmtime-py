from ctypes import byref, POINTER, c_int
from . import _ffi as ffi
import ctypes
from typing import Optional


class WasmtimeError(Exception):
    _ptr: "Optional[ctypes._Pointer[ffi.wasmtime_error_t]]"
    _message: Optional[str]

    def __init__(self, message: str):
        self._message = message
        self._ptr = None

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer") -> 'WasmtimeError':
        from . import _ffi as ffi
        if not isinstance(ptr, POINTER(ffi.wasmtime_error_t)):
            raise TypeError("wrong pointer type")

        exit_code = c_int(0)
        if ffi.wasmtime_error_exit_status(ptr, byref(exit_code)):
            exit_trap: ExitTrap = ExitTrap.__new__(ExitTrap)
            exit_trap._ptr = ptr
            exit_trap._message = None
            exit_trap.code = exit_code.value
            return exit_trap

        err: WasmtimeError = cls.__new__(cls)
        err._ptr = ptr
        err._message = None
        return err

    def __str__(self) -> str:
        if self._message:
            return self._message
        message_vec = ffi.wasm_byte_vec_t()
        ffi.wasmtime_error_message(self._ptr, byref(message_vec))
        message = ffi.to_str(message_vec)
        ffi.wasm_byte_vec_delete(byref(message_vec))
        return message

    def __del__(self) -> None:
        if hasattr(self, '_ptr') and self._ptr:
            ffi.wasmtime_error_delete(self._ptr)


class ExitTrap(WasmtimeError):
    """
    A special type of `WasmtimeError` which represents the process exiting via
    WASI's `proc_exit` function call.

    Whenever a WASI program exits via `proc_exit` a trap is raised, but the
    trap will have this type instead of `WasmtimeError`, so you can catch just
    this type instead of all traps (if desired). Exit traps have a `code`
    associated with them which is the exit code provided at exit.

    Note that `ExitTrap` is a subclass of `WasmtimeError`, so if you catch a
    trap you'll also catch `ExitTrap`.
    """
    code: int
    pass
