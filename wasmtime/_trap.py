from . import _ffi as ffi
from enum import Enum
from ctypes import byref, POINTER
import ctypes
from typing import Optional, Any, List
from wasmtime import Managed


class TrapCode(Enum):
    # The current stack space was exhausted.
    STACK_OVERFLOW = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_STACK_OVERFLOW.value
    # An out-of-bounds memory access.
    MEMORY_OUT_OF_BOUNDS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_MEMORY_OUT_OF_BOUNDS.value
    # A wasm atomic operation was presented with a not-naturally-aligned linear-memory address.
    HEAP_MISALIGNED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_HEAP_MISALIGNED.value
    # An out-of-bounds access to a table.
    TABLE_OUT_OF_BOUNDS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_TABLE_OUT_OF_BOUNDS.value
    # Indirect call to a null table entry.
    INDIRECT_CALL_TO_NULL = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INDIRECT_CALL_TO_NULL.value
    # Signature mismatch on indirect call.
    BAD_SIGNATURE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_BAD_SIGNATURE.value
    # An integer arithmetic operation caused an overflow.
    INTEGER_OVERFLOW = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INTEGER_OVERFLOW.value
    # An integer division by zero.
    INTEGER_DIVISION_BY_ZERO = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INTEGER_DIVISION_BY_ZERO.value
    # Failed float-to-int conversion.
    BAD_CONVERSION_TO_INTEGER = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_BAD_CONVERSION_TO_INTEGER.value
    # Code that was supposed to have been unreachable was reached.
    UNREACHABLE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_UNREACHABLE_CODE_REACHED.value
    # Execution has potentially run too long and may be interrupted.
    INTERRUPT = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INTERRUPT.value
    # Execution has run out of the configured fuel amount.
    OUT_OF_FUEL = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_OUT_OF_FUEL.value
    # Atomic wait on non-shared memory.
    ATOMIC_WAIT_NON_SHARED_MEMORY = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_ATOMIC_WAIT_NON_SHARED_MEMORY.value
    # Call to a null reference.
    NULL_REFERENCE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_NULL_REFERENCE.value
    # Attempt to access beyond the bounds of an array.
    ARRAY_OUT_OF_BOUNDS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_ARRAY_OUT_OF_BOUNDS.value
    # Attempted an allocation that was too large to succeed.
    ALLOCATION_TOO_LARGE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_ALLOCATION_TOO_LARGE.value
    # Attempted to cast a reference to a type that it is not an instance of.
    CAST_FAILURE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CAST_FAILURE.value
    # A component tried to call another component in violation of the reentrance rules.
    CANNOT_ENTER_COMPONENT = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CANNOT_ENTER_COMPONENT.value
    # Async-lifted export failed to produce a result before returning STATUS_DONE.
    NO_ASYNC_RESULT = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_NO_ASYNC_RESULT.value
    # Suspending to a tag for which there is no active handler.
    UNHANDLED_TAG = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_UNHANDLED_TAG.value
    # Attempt to resume a continuation twice.
    CONTINUATION_ALREADY_CONSUMED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CONTINUATION_ALREADY_CONSUMED.value
    # A Pulley opcode was executed that was disabled at compile time.
    DISABLED_OPCODE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_DISABLED_OPCODE.value
    # Async event loop deadlocked.
    ASYNC_DEADLOCK = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_ASYNC_DEADLOCK.value
    # A component tried to call an import when it was not allowed to.
    CANNOT_LEAVE_COMPONENT = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CANNOT_LEAVE_COMPONENT.value
    # A synchronous task attempted a potentially blocking call before returning.
    CANNOT_BLOCK_SYNC_TASK = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CANNOT_BLOCK_SYNC_TASK.value
    # A component tried to lift a char with an invalid bit pattern.
    INVALID_CHAR = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INVALID_CHAR.value
    # Debug assertion: string encoding not finished.
    DEBUG_ASSERT_STRING_ENCODING_FINISHED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_DEBUG_ASSERT_STRING_ENCODING_FINISHED.value
    # Debug assertion: equal code units.
    DEBUG_ASSERT_EQUAL_CODE_UNITS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_DEBUG_ASSERT_EQUAL_CODE_UNITS.value
    # Debug assertion: pointer aligned.
    DEBUG_ASSERT_POINTER_ALIGNED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_DEBUG_ASSERT_POINTER_ALIGNED.value
    # Debug assertion: upper bits unset.
    DEBUG_ASSERT_UPPER_BITS_UNSET = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_DEBUG_ASSERT_UPPER_BITS_UNSET.value
    # A component tried to lift or lower a string past the end of its memory.
    STRING_OUT_OF_BOUNDS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_STRING_OUT_OF_BOUNDS.value
    # A component tried to lift or lower a list past the end of its memory.
    LIST_OUT_OF_BOUNDS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_LIST_OUT_OF_BOUNDS.value
    # A component used an invalid discriminant when lowering a variant value.
    INVALID_DISCRIMINANT = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_INVALID_DISCRIMINANT.value
    # A component passed an unaligned pointer when lifting or lowering a value.
    UNALIGNED_POINTER = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_UNALIGNED_POINTER.value
    # task.cancel invoked in an invalid way.
    TASK_CANCEL_NOT_CANCELLED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_TASK_CANCEL_NOT_CANCELLED.value
    # task.cancel or task.return called too many times.
    TASK_CANCEL_OR_RETURN_TWICE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_TASK_CANCEL_OR_RETURN_TWICE.value
    # subtask.cancel invoked after the subtask already finished.
    SUBTASK_CANCEL_AFTER_TERMINAL = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_SUBTASK_CANCEL_AFTER_TERMINAL.value
    # task.return invoked with an invalid type.
    TASK_RETURN_INVALID = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_TASK_RETURN_INVALID.value
    # waitable-set.drop invoked on a waitable set with waiters.
    WAITABLE_SET_DROP_HAS_WAITERS = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_WAITABLE_SET_DROP_HAS_WAITERS.value
    # subtask.drop invoked on a subtask that hasn't resolved yet.
    SUBTASK_DROP_NOT_RESOLVED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_SUBTASK_DROP_NOT_RESOLVED.value
    # thread.new-indirect invoked with a function that has an invalid type.
    THREAD_NEW_INDIRECT_INVALID_TYPE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_THREAD_NEW_INDIRECT_INVALID_TYPE.value
    # thread.new-indirect invoked with an uninitialized function reference.
    THREAD_NEW_INDIRECT_UNINITIALIZED = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_THREAD_NEW_INDIRECT_UNINITIALIZED.value
    # Backpressure-related intrinsics overflowed the built-in counter.
    BACKPRESSURE_OVERFLOW = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_BACKPRESSURE_OVERFLOW.value
    # Invalid code returned from the callback of an async-lifted function.
    UNSUPPORTED_CALLBACK_CODE = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_UNSUPPORTED_CALLBACK_CODE.value
    # Cannot resume a thread which is not suspended.
    CANNOT_RESUME_THREAD = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CANNOT_RESUME_THREAD.value
    # Cannot issue a read/write on a future/stream while there is a pending operation.
    CONCURRENT_FUTURE_STREAM_OP = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_CONCURRENT_FUTURE_STREAM_OP.value
    # A reference count overflowed the built-in counter.
    REFERENCE_COUNT_OVERFLOW = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_REFERENCE_COUNT_OVERFLOW.value
    # A stream operation was performed with a buffer that was too large.
    STREAM_OP_TOO_BIG = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_STREAM_OP_TOO_BIG.value
    # A waitable was used both synchronously and asynchronously.
    WAITABLE_SYNC_AND_ASYNC = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_WAITABLE_SYNC_AND_ASYNC.value
    # An exception was thrown and never caught.
    UNCAUGHT_EXCEPTION = ffi.wasmtime_trap_code_enum.WASMTIME_TRAP_CODE_UNCAUGHT_EXCEPTION.value


class Trap(Exception, Managed["ctypes._Pointer[ffi.wasm_trap_t]"]):

    def __init__(self, message: str):
        """
        Creates a new trap with the given `message`
        """

        vec = message.encode('utf-8')
        self._set_ptr(ffi.wasmtime_trap_new(ctypes.create_string_buffer(vec), len(vec)))

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
