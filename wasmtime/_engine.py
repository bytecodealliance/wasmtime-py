from . import _ffi as ffi
from wasmtime import Config, WasmtimeError


class Engine:
    def __init__(self, config: Config = None):
        if config is None:
            self.__ptr__ = ffi.wasm_engine_new()
        elif not isinstance(config, Config):
            raise TypeError("expected Config")
        elif not hasattr(config, '__ptr__'):
            raise WasmtimeError("Config already used")
        else:
            ptr = config.__ptr__
            delattr(config, '__ptr__')
            self.__ptr__ = ffi.wasm_engine_new_with_config(ptr)

    def __del__(self) -> None:
        if hasattr(self, '__ptr__'):
            ffi.wasm_engine_delete(self.__ptr__)
