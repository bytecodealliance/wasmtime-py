from ._ffi import *
from ctypes import *
from wasmtime import Config, WasmtimeError

dll.wasm_engine_new.restype = P_wasm_engine_t
dll.wasm_engine_new_with_config.restype = P_wasm_engine_t


class Engine:
    def __init__(self, config: Config = None):
        if config is None:
            self.__ptr__ = dll.wasm_engine_new()
        elif not isinstance(config, Config):
            raise TypeError("expected Config")
        elif not hasattr(config, '__ptr__'):
            raise WasmtimeError("Config already used")
        else:
            ptr = config.__ptr__
            delattr(config, '__ptr__')
            self.__ptr__ = dll.wasm_engine_new_with_config(ptr)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_engine_delete(self.__ptr__)
