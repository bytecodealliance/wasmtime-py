from . import _ffi as ffi
from ctypes import *
from wasmtime import Store
import typing


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
        ptr = ffi.wasm_trap_new(store.__ptr__, byref(message_raw))
        if not ptr:
            raise WasmtimeError("failed to create trap")
        self.__ptr__ = ptr

    @classmethod
    def __from_ptr__(cls, ptr):
        if not isinstance(ptr, POINTER(ffi.wasm_trap_t)):
            raise TypeError("wrong pointer type")
        trap = cls.__new__(cls)
        trap.__ptr__ = ptr
        return trap

    @property
    def message(self) -> str:
        """
        Returns the message for this trap
        """

        message = ffi.wasm_byte_vec_t()
        ffi.wasm_trap_message(self.__ptr__, byref(message))
        # subtract one to chop off the trailing nul byte
        message.size -= 1
        ret = ffi.to_str(message)
        message.size += 1
        ffi.wasm_byte_vec_delete(byref(message))
        return ret

    @property
    def frames(self) -> typing.List["Frame"]:
        frames = FrameList()
        ffi.wasm_trap_trace(self.__ptr__, byref(frames.vec))
        ret = []
        for i in range(0, frames.vec.size):
            ret.append(Frame.__from_ptr__(frames.vec.data[i], frames))
        return ret

    def __str__(self):
        return self.message

    def __del__(self):
        if hasattr(self, '__ptr__'):
            ffi.wasm_trap_delete(self.__ptr__)


class Frame:
    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner) -> "Frame":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_frame_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def func_index(self) -> int:
        """
        Returns the function index this frame corresponds to in its wasm module
        """

        return ffi.wasm_frame_func_index(self.__ptr__)

    @property
    def func_name(self) -> typing.Optional[str]:
        """
        Returns the name of the function this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = ffi.wasmtime_frame_func_name(self.__ptr__)
        if ptr:
            return ffi.to_str(ptr.contents)
        else:
            return None

    @property
    def module_name(self) -> typing.Optional[str]:
        """
        Returns the name of the module this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = ffi.wasmtime_frame_module_name(self.__ptr__)
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

        return ffi.wasm_frame_module_offset(self.__ptr__)

    @property
    def func_offset(self) -> int:
        """
        Returns the offset of this frame's program counter into the original
        wasm function.
        """

        return ffi.wasm_frame_func_offset(self.__ptr__)

    def __del__(self):
        if self.__owner__ is None:
            ffi.wasm_frame_delete(self.__ptr__)


class FrameList:
    def __init__(self):
        self.vec = ffi.wasm_frame_vec_t(0, None)

    def __del__(self):
        ffi.wasm_frame_vec_delete(byref(self.vec))
