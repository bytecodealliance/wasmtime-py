from wasmtime import Config, WasmtimeError, Managed
from typing import Optional
import ctypes

from . import _bindings


class Engine(Managed["ctypes._Pointer[_bindings.wasm_engine_t]"]):

    def __init__(self, config: Optional[Config] = None):
        if config is None:
            self._set_ptr(_bindings.wasm_engine_new())
        elif not isinstance(config, Config):
            raise TypeError("expected Config")
        else:
            ptr = config._consume()
            self._set_ptr(_bindings.wasm_engine_new_with_config(ptr))

    def _delete(self, ptr: "ctypes._Pointer[_bindings.wasm_engine_t]") -> None:
        _bindings.wasm_engine_delete(ptr)

    def increment_epoch(self) -> None:
        _bindings.wasmtime_engine_increment_epoch(self.ptr())

    def is_pulley(self) -> bool:
        return _bindings.wasmtime_engine_is_pulley(self.ptr())
