from . import _ffi as ffi
from ctypes import *
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

    def __init__(self) -> None:
        self.__ptr__ = ffi.wasm_config_new()

    @setter_property
    def debug_info(self, enable: bool) -> None:
        """
        Configures whether DWARF debug information is emitted for the generated
        code. This can improve profiling and the debugging experience.
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_debug_info_set(self.__ptr__, enable)

    @setter_property
    def wasm_threads(self, enable: bool) -> None:
        """
        Configures whether the wasm [threads proposal] is enabled.

        [threads proposal]: https://github.com/webassembly/threads
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_threads_set(self.__ptr__, enable)

    @setter_property
    def wasm_reference_types(self, enable: bool) -> None:
        """
        Configures whether the wasm [reference types proposal] is enabled.

        [reference types proposal]: https://github.com/webassembly/reference-types
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_reference_types_set(self.__ptr__, enable)

    @setter_property
    def wasm_simd(self, enable: bool) -> None:
        """
        Configures whether the wasm [SIMD proposal] is enabled.

        [SIMD proposal]: https://github.com/webassembly/simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_simd_set(self.__ptr__, enable)

    @setter_property
    def wasm_bulk_memory(self, enable: bool) -> None:
        """
        Configures whether the wasm [bulk memory proposal] is enabled.

        [bulk memory proposal]: https://github.com/webassembly/bulk-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_bulk_memory_set(self.__ptr__, enable)

    @setter_property
    def wasm_multi_value(self, enable: bool) -> None:
        """
        Configures whether the wasm [multi value proposal] is enabled.

        [multi value proposal]: https://github.com/webassembly/multi-value
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_multi_value_set(self.__ptr__, enable)

    @setter_property
    def strategy(self, strategy: str) -> None:
        """
        Configures the compilation strategy used for wasm code.

        Acceptable values for `strategy` are:

        * `"auto"`
        * `"cranelift"`
        * `"lightbeam"`
        """

        if strategy == "auto":
            error = ffi.wasmtime_config_strategy_set(self.__ptr__, 0)
        elif strategy == "cranelift":
            error = ffi.wasmtime_config_strategy_set(self.__ptr__, 1)
        elif strategy == "lightbeam":
            error = ffi.wasmtime_config_strategy_set(self.__ptr__, 2)
        else:
            raise WasmtimeError("unknown strategy: " + str(strategy))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @setter_property
    def cranelift_debug_verifier(self, enable: bool) -> None:
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_cranelift_debug_verifier_set(self.__ptr__, enable)

    @setter_property
    def cranelift_opt_level(self, opt_level: str) -> None:
        if opt_level == "none":
            ffi.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 0)
        elif opt_level == "speed":
            ffi.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 1)
        elif opt_level == "speed_and_size":
            ffi.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 2)
        else:
            raise WasmtimeError("unknown opt level: " + str(opt_level))

    @setter_property
    def profiler(self, profiler: str) -> None:
        if profiler == "none":
            error = ffi.wasmtime_config_profiler_set(self.__ptr__, 0)
        elif profiler == "jitdump":
            error = ffi.wasmtime_config_profiler_set(self.__ptr__, 1)
        else:
            raise WasmtimeError("unknown profiler: " + str(profiler))
        if error:
            raise WasmtimeError.__from_ptr__(error)

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
            error = ffi.wasmtime_config_cache_config_load(self.__ptr__, None)
        elif isinstance(enabled, str):
            error = ffi.wasmtime_config_cache_config_load(self.__ptr__,
                                                          c_char_p(enabled.encode('utf-8')))
        else:
            raise TypeError("expected string or bool")
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @setter_property
    def interruptable(self, enabled: bool) -> None:
        """
        Configures whether wasm execution can be interrupted via interrupt
        handles.
        """

        if enabled:
            val = 1
        else:
            val = 0
        ffi.wasmtime_config_interruptable_set(self.__ptr__, val)

    def __del__(self) -> None:
        if hasattr(self, '__ptr__'):
            ffi.wasm_config_delete(self.__ptr__)
