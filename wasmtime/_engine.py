from . import _ffi as ffi
from wasmtime import Config, WasmtimeError


class Engine:
    def __init__(self, config: Config = None):
        if config is None:
            self._ptr = ffi.wasm_engine_new()
        elif not isinstance(config, Config):
            raise TypeError("expected Config")
        elif not hasattr(config, '_ptr'):
            raise WasmtimeError("Config already used")
        else:
            ptr = config._ptr
            delattr(config, '_ptr')
            self._ptr = ffi.wasm_engine_new_with_config(ptr)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasm_engine_delete(self._ptr)
