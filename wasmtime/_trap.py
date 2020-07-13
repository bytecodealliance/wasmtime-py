from . import _ffi as ffi
from ctypes import byref, POINTER, pointer, c_int
from wasmtime import Store, WasmtimeError
from typing import Optional, Any, List


class Trap(Exception):
    def __init__(self, store: Store, message: str):
        """
        Creates a new trap in `store` with the given `message`
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(message, str):
            raise TypeError("expected a string")
        message_raw = ffi.str_to_name(message, trailing_nul=True)
        ptr = ffi.wasm_trap_new(store._ptr, byref(message_raw))
        if not ptr:
            raise WasmtimeError("failed to create trap")
        self._ptr = ptr

    @classmethod
    def _from_ptr(cls, ptr: "pointer[ffi.wasm_trap_t]") -> "Trap":
        if not isinstance(ptr, POINTER(ffi.wasm_trap_t)):
            raise TypeError("wrong pointer type")
        exit_code = c_int(0)
        if ffi.wasmtime_trap_exit_status(ptr, byref(exit_code)):
            exit_trap: ExitTrap = ExitTrap.__new__(ExitTrap)
            exit_trap._ptr = ptr
            exit_trap.code = exit_code.value
            return exit_trap
        else:
            trap: Trap = cls.__new__(cls)
            trap._ptr = ptr
            return trap

    @property
    def message(self) -> str:
        """
        Returns the message for this trap
        """

        message = ffi.wasm_byte_vec_t()
        ffi.wasm_trap_message(self._ptr, byref(message))
        # subtract one to chop off the trailing nul byte
        message.size -= 1
        ret = ffi.to_str(message)
        message.size += 1
        ffi.wasm_byte_vec_delete(byref(message))
        return ret

    @property
    def frames(self) -> List["Frame"]:
        frames = FrameList()
        ffi.wasm_trap_trace(self._ptr, byref(frames.vec))
        ret = []
        for i in range(0, frames.vec.size):
            ret.append(Frame._from_ptr(frames.vec.data[i], frames))
        return ret

    def __str__(self) -> str:
        return self.message

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasm_trap_delete(self._ptr)


class ExitTrap(Trap):
    """
    A special type of `Trap` which represents the process exiting via WASI's
    `proc_exit` function call.

    Whenever a WASI program exits via `proc_exit` a trap is raised, but the
    trap will have this type instead of `Trap`, so you can catch just this
    type instead of all traps (if desired). Exit traps have a `code` associated
    with them which is the exit code provided at exit.

    Note that `ExitTrap` is a subclass of `Trap`, so if you catch a trap you'll
    also catch `ExitTrap`.
    """
    code: int
    pass


class Frame:
    _ptr: "pointer[ffi.wasm_frame_t]"
    _owner: Optional[Any]

    @classmethod
    def _from_ptr(cls, ptr: "pointer[ffi.wasm_frame_t]", owner: Optional[Any]) -> "Frame":
        ty: "Frame" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_frame_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty._owner = owner
        return ty

    @property
    def func_index(self) -> int:
        """
        Returns the function index this frame corresponds to in its wasm module
        """

        return ffi.wasm_frame_func_index(self._ptr)

    @property
    def func_name(self) -> Optional[str]:
        """
        Returns the name of the function this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = ffi.wasmtime_frame_func_name(self._ptr)
        if ptr:
            return ffi.to_str(ptr.contents)
        else:
            return None

    @property
    def module_name(self) -> Optional[str]:
        """
        Returns the name of the module this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = ffi.wasmtime_frame_module_name(self._ptr)
        if ptr:
            return ffi.to_str(ptr.contents)
        else:
            return None

    @property
    def module_offset(self) -> int:
        """
        Returns the offset of this frame's program counter into the original
        wasm source module.
        """

        return ffi.wasm_frame_module_offset(self._ptr)

    @property
    def func_offset(self) -> int:
        """
        Returns the offset of this frame's program counter into the original
        wasm function.
        """

        return ffi.wasm_frame_func_offset(self._ptr)

    def __del__(self) -> None:
        if self._owner is None:
            ffi.wasm_frame_delete(self._ptr)


class FrameList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_frame_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_frame_vec_delete(byref(self.vec))
