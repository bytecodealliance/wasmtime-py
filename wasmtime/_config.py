from . import _ffi as ffi
from ctypes import *
import ctypes
from wasmtime import WasmtimeError
import typing


def setter_property(fset: typing.Callable) -> property:
    prop = property(fset=fset)
    if fset.__doc__:
        prop.__doc__ = fset.__doc__
        prop.__doc__ += "\n\n        Note that this field can only be set, it cannot be read"
    return prop


class Config:
    """
    Global configuration, used to create an `Engine`.

    A `Config` houses a number of configuration options which tweaks how wasm
    code is compiled or generated.
    """

    _ptr: "ctypes._Pointer[ffi.wasm_config_t]"

    def __init__(self) -> None:
        self._ptr = ffi.wasm_config_new()

    @setter_property
    def debug_info(self, enable: bool) -> None:
        """
        Configures whether DWARF debug information is emitted for the generated
        code. This can improve profiling and the debugging experience.
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_debug_info_set(self._ptr, enable)

    @setter_property
    def wasm_threads(self, enable: bool) -> None:
        """
        Configures whether the wasm [threads proposal] is enabled.

        [threads proposal]: https://github.com/webassembly/threads
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_threads_set(self._ptr, enable)

    @setter_property
    def wasm_reference_types(self, enable: bool) -> None:
        """
        Configures whether the wasm [reference types proposal] is enabled.

        [reference types proposal]: https://github.com/webassembly/reference-types
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_reference_types_set(self._ptr, enable)

    @setter_property
    def wasm_simd(self, enable: bool) -> None:
        """
        Configures whether the wasm [SIMD proposal] is enabled.

        [SIMD proposal]: https://github.com/webassembly/simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_simd_set(self._ptr, enable)

    @setter_property
    def wasm_bulk_memory(self, enable: bool) -> None:
        """
        Configures whether the wasm [bulk memory proposal] is enabled.

        [bulk memory proposal]: https://github.com/webassembly/bulk-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_bulk_memory_set(self._ptr, enable)

    @setter_property
    def wasm_multi_value(self, enable: bool) -> None:
        """
        Configures whether the wasm [multi value proposal] is enabled.

        [multi value proposal]: https://github.com/webassembly/multi-value
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_multi_value_set(self._ptr, enable)

    @setter_property
    def wasm_multi_memory(self, enable: bool) -> None:
        """
        Configures whether the wasm [multi memory proposal] is enabled.

        [multi memory proposal]: https://github.com/webassembly/multi-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_multi_memory_set(self._ptr, enable)

    @setter_property
    def wasm_memory64(self, enable: bool) -> None:
        """
        Configures whether the wasm [memory64 proposal] is enabled.

        [memory64 proposal]: https://github.com/webassembly/memory64
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_memory64_set(self._ptr, enable)

    @setter_property
    def strategy(self, strategy: str) -> None:
        """
        Configures the compilation strategy used for wasm code.

        Acceptable values for `strategy` are:

        * `"auto"`
        * `"cranelift"`
        """

        if strategy == "auto":
            ffi.wasmtime_config_strategy_set(self._ptr, 0)
        elif strategy == "cranelift":
            ffi.wasmtime_config_strategy_set(self._ptr, 1)
        else:
            raise WasmtimeError("unknown strategy: " + str(strategy))

    @setter_property
    def cranelift_debug_verifier(self, enable: bool) -> None:
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_cranelift_debug_verifier_set(self._ptr, enable)

    @setter_property
    def cranelift_opt_level(self, opt_level: str) -> None:
        if opt_level == "none":
            ffi.wasmtime_config_cranelift_opt_level_set(self._ptr, 0)
        elif opt_level == "speed":
            ffi.wasmtime_config_cranelift_opt_level_set(self._ptr, 1)
        elif opt_level == "speed_and_size":
            ffi.wasmtime_config_cranelift_opt_level_set(self._ptr, 2)
        else:
            raise WasmtimeError("unknown opt level: " + str(opt_level))

    @setter_property
    def profiler(self, profiler: str) -> None:
        if profiler == "none":
            ffi.wasmtime_config_profiler_set(self._ptr, 0)
        elif profiler == "jitdump":
            ffi.wasmtime_config_profiler_set(self._ptr, 1)
        else:
            raise WasmtimeError("unknown profiler: " + str(profiler))

    @setter_property
    def cache(self, enabled: typing.Union[bool, str]) -> None:
        """
        Configures whether code caching is enabled for this `Config`.

        The value `True` can be passed in here to enable the default caching
        configuration and location, or a path to a file can be passed in which
        is a path to a TOML configuration file for the cache.

        More information about cache configuration can be found at
        https://bytecodealliance.github.io/wasmtime/cli-cache.html
        """

        if isinstance(enabled, bool):
            if not enabled:
                raise WasmtimeError("caching cannot be explicitly disabled")
            error = ffi.wasmtime_config_cache_config_load(self._ptr, None)
        elif isinstance(enabled, str):
            error = ffi.wasmtime_config_cache_config_load(self._ptr,
                                                          c_char_p(enabled.encode('utf-8')))
        else:
            raise TypeError("expected string or bool")
        if error:
            raise WasmtimeError._from_ptr(error)

    @setter_property
    def epoch_interruption(self, enabled: bool) -> None:
        """
        Configures whether wasm execution can be interrupted via epoch
        increments.
        """

        if enabled:
            val = 1
        else:
            val = 0
        ffi.wasmtime_config_epoch_interruption_set(self._ptr, val)

    @setter_property
    def consume_fuel(self, instances: bool) -> None:
        """
        Configures whether wasm code will consume *fuel* as part of its
        execution.

        Fuel consumption allows WebAssembly to trap when fuel runs out.
        Currently stores start with 0 fuel if this is enabled.
        """
        if not isinstance(instances, bool):
            raise TypeError('expected an bool')
        ffi.wasmtime_config_consume_fuel_set(self._ptr, instances)

    @setter_property
    def parallel_compilation(self, enable: bool) -> None:
        """
        Configures whether parallel compilation is enabled for functions
        within a module.

        This is enabled by default.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_parallel_compilation_set(self._ptr, enable)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasm_config_delete(self._ptr)
