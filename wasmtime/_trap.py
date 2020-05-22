from ._ffi import *
from ctypes import *
from wasmtime import Store

dll.wasm_trap_new.restype = P_wasm_trap_t
dll.wasm_frame_func_index.restype = c_uint32
dll.wasmtime_frame_func_name.restype = POINTER(wasm_byte_vec_t)
dll.wasmtime_frame_module_name.restype = POINTER(wasm_byte_vec_t)
dll.wasm_frame_module_offset.restype = c_size_t
dll.wasm_frame_func_offset.restype = c_size_t


class Trap(Exception):
    def __init__(self, store, message):
        """
        Creates a new trap in `store` with the given `message`
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(message, str):
            raise TypeError("expected a string")
        message_raw = str_to_name(message, trailing_nul=True)
        ptr = dll.wasm_trap_new(store.__ptr__, byref(message_raw))
        if not ptr:
            raise WasmtimeError("failed to create trap")
        self.__ptr__ = ptr

    @classmethod
    def __from_ptr__(cls, ptr):
        if not isinstance(ptr, P_wasm_trap_t):
            raise TypeError("wrong pointer type")
        trap = cls.__new__(cls)
        trap.__ptr__ = ptr
        return trap

    @property
    def message(self):
        """
        Returns the message for this trap
        """

        message = wasm_byte_vec_t()
        dll.wasm_trap_message(self.__ptr__, byref(message))
        # subtract one to chop off the trailing nul byte
        message.size -= 1
        ret = message.to_str()
        message.size += 1
        dll.wasm_byte_vec_delete(byref(message))
        return ret

    @property
    def frames(self):
        frames = FrameList()
        dll.wasm_trap_trace(self.__ptr__, byref(frames.vec))
        ret = []
        for i in range(0, frames.vec.size):
            ret.append(Frame.__from_ptr__(frames.vec.data[i], frames))
        return ret

    def __str__(self):
        frames = self.frames
        message = self.message
        if len(frames) > 0:
            message += "\nwasm backtrace:\n"
            for i, frame in enumerate(frames):
                module = frame.module_name or '<unknown>'
                default_func_name = '<wasm function %d>' % frame.func_index
                func = frame.func_name or default_func_name
                message += "  {}: {:#6x} - {}!{}\n".format(i, frame.module_offset, module, func)
        return message

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_trap_delete(self.__ptr__)


class Frame:
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_frame_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def func_index(self):
        """
        Returns the function index this frame corresponds to in its wasm module
        """

        return dll.wasm_frame_func_index(self.__ptr__)

    @property
    def func_name(self):
        """
        Returns the name of the function this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = dll.wasmtime_frame_func_name(self.__ptr__)
        if ptr:
            return ptr.contents.to_str()
        else:
            return None

    @property
    def module_name(self):
        """
        Returns the name of the module this frame corresponds to

        May return `None` if no name can be inferred
        """

        ptr = dll.wasmtime_frame_module_name(self.__ptr__)
        if ptr:
            return ptr.contents.to_str()
        else:
            return None

    @property
    def module_offset(self):
        """
        Returns the offset of this frame's program counter into the original
        wasm source module.
        """

        return dll.wasm_frame_module_offset(self.__ptr__)

    @property
    def func_offset(self):
        """
        Returns the offset of this frame's program counter into the original
        wasm function.
        """

        return dll.wasm_frame_func_offset(self.__ptr__)

    def __del__(self):
        if self.__owner__ is None:
            dll.wasm_frame_delete(self.__ptr__)


class FrameList:
    def __init__(self):
        self.vec = wasm_frame_vec_t(0, None)

    def __del__(self):
        dll.wasm_frame_vec_delete(byref(self.vec))
