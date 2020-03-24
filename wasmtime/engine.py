from .ffi import *
from ctypes import *
from wasmtime import Config

class Engine:
    def __init__(self, config = None):
        if config is None:
            self.__ptr__ = cast(dll.wasm_engine_new(), P_wasm_engine_t)
        elif not isinstance(config, Config):
            raise TypeError("expected Config")
        elif config.__ptr__ is None:
            raise RuntimeError("Config already used")
        else:
            ptr = config.__ptr__
            config.__ptr__ = None
            self.__ptr__ = cast(dll.wasm_engine_new_with_config(ptr), P_wasm_engine_t)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_engine_delete(self.__ptr__)
