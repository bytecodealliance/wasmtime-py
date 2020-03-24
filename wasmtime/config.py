from .ffi import *
from ctypes import *

class Config:
    def __init__(self):
        self.__ptr__ = cast(dll.wasm_config_new(), P_wasm_config_t)

    def __del__(self):
        if self.__ptr__ is not None:
            dll.wasm_config_delete(self.__ptr__)
