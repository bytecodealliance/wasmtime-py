from . import _ffi as ffi
from enum import Enum
from ctypes import byref, POINTER
import ctypes
from typing import Optional, Any, List
from wasmtime import Managed


class TrapCode(Enum):
    # The current stack space was exhausted.
    STACK_OVERFLOW = 0
    # An out-of-bounds memory access.
    MEMORY_OUT_OF_BOUNDS = 1
    # A wasm atomic operation was presented with a not-naturally-aligned linear-memory address.
    HEAP_MISALIGNED = 2
    # An out-of-bounds access to a table.
    TABLE_OUT_OF_BOUNDS = 3
    # Indirect call to a null table entry.
    INDIRECT_CALL_TO_NULL = 4
    # Signature mismatch on indirect call.
    BAD_SIGNATURE = 5
    # An integer arithmetic operation caused an overflow.
    INTEGER_OVERFLOW = 6
    # An integer division by zero.
    INTEGER_DIVISION_BY_ZERO = 7
    # Failed float-to-int conversion.
    BAD_CONVERSION_TO_INTEGER = 8
    # Code that was supposed to have been unreachable was reached.
    UNREACHABLE = 9
    # Execution has potentially run too long and may be interrupted.
    INTERRUPT = 10


class Trap(Exception, Managed["ctypes._Pointer[ffi.wasm_trap_t]"]):

    def __init__(self, message: str):
        """
        Creates a new trap with the given `message`
        """

        vec = message.encode('utf-8')
        self._set_ptr(ffi.wasmtime_trap_new(ffi.create_string_buffer(vec), len(vec)))

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_trap_t]") -> None:
        ffi.wasm_trap_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_trap_t]") -> "Trap":
        if not isinstance(ptr, POINTER(ffi.wasm_trap_t)):
            raise TypeError("wrong pointer type")
        trap: Trap = cls.__new__(cls)
        trap._set_ptr(ptr)
        return trap

    @property
    def message(self) -> str:
        """
        Returns the message for this trap
        """

        message = ffi.wasm_byte_vec_t()
        ffi.wasm_trap_message(self.ptr(), byref(message))
        # subtract one to chop off the trailing nul byte
        message.size -= 1
        ret = ffi.to_str(message)
        message.size += 1
        ffi.wasm_byte_vec_delete(byref(message))
        return ret

    @property
    def frames(self) -> List["Frame"]:
        frames = FrameList(self)
        ffi.wasm_trap_trace(self.ptr(), byref(frames.vec))
        ret = []
        for i in range(0, frames.vec.size):
            ret.append(Frame._from_ptr(frames.vec.data[i], frames))
        return ret

    @property
    def trap_code(self) -> Optional[TrapCode]:
        """
        Returns an optional `TrapCode` that corresponds to why this trap
        happened.

        Note that `None` may be returned for manually created traps which do
        not have an associated code with them.
        """
        code = ffi.wasmtime_trap_code_t()
        if ffi.wasmtime_trap_code(self.ptr(), byref(code)):
            return TrapCode(code.value)
        return None

    def __str__(self) -> str:
        return self.message


class Frame(Managed["ctypes._Pointer[ffi.wasm_frame_t]"]):
    _owner: Optional[Any]

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_frame_t]", owner: Optional[Any]) -> "Frame":
        if not isinstance(ptr, POINTER(ffi.wasm_frame_t)):
            raise TypeError("wrong pointer type")
        ty: "Frame" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_frame_t]") -> None:
        if self._owner is None:
            ffi.wasm_frame_delete(ptr)

    @property
    def func_index(self) -> int:
        """
        Returns the function index this frame corresponds to in its wasm module
        """

        return ffi.wasm_frame_func_index(self.ptr())

    @property
    def func_name(self) -> Optional[str]:
        """
        Returns the name of the function this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = ffi.wasmtime_frame_func_name(self.ptr())
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

        ptr = ffi.wasmtime_frame_module_name(self.ptr())
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

        return ffi.wasm_frame_module_offset(self.ptr())

    @property
    def func_offset(self) -> int:
        """
        Returns the offset of this frame's program counter into the original
        wasm function.
        """

        return ffi.wasm_frame_func_offset(self.ptr())


class FrameList:
    owner: Any

    def __init__(self, owner: Any) -> None:
        self.vec = ffi.wasm_frame_vec_t(0, None)
        self.owner = owner

    def __del__(self) -> None:
        ffi.wasm_frame_vec_delete(byref(self.vec))
