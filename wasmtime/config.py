from .ffi import *
from ctypes import *

dll.wasm_config_new.restype = P_wasm_config_t

class Config:
    def __init__(self):
        self.__ptr__ = dll.wasm_config_new()

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_config_delete(self.__ptr__)
