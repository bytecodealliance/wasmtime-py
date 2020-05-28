from ._ffi import *
from ctypes import *
from wasmtime import WasmtimeError
__all__ = [
    "Config",
    "setter_property",
]


dll.wasm_config_new.restype = P_wasm_config_t
dll.wasmtime_config_strategy_set.restype = P_wasmtime_error_t
dll.wasmtime_config_profiler_set.restype = P_wasmtime_error_t
dll.wasmtime_config_cache_config_load.restype = P_wasmtime_error_t


def setter_property(fset):
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

    def __init__(self):
        self.__ptr__ = dll.wasm_config_new()

    @setter_property
    def debug_info(self, enable):
        """
        Configures whether DWARF debug information is emitted for the generated
        code. This can improve profiling and the debugging experience.
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_debug_info_set(self.__ptr__, enable)

    @setter_property
    def wasm_threads(self, enable):
        """
        Configures whether the wasm [threads proposal] is enabled.

        [threads proposal]: https://github.com/webassembly/threads
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_threads_set(self.__ptr__, enable)

    @setter_property
    def wasm_reference_types(self, enable):
        """
        Configures whether the wasm [reference types proposal] is enabled.

        [reference types proposal]: https://github.com/webassembly/reference-types
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_reference_types_set(self.__ptr__, enable)

    @setter_property
    def wasm_simd(self, enable):
        """
        Configures whether the wasm [SIMD proposal] is enabled.

        [SIMD proposal]: https://github.com/webassembly/simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_simd_set(self.__ptr__, enable)

    @setter_property
    def wasm_bulk_memory(self, enable):
        """
        Configures whether the wasm [bulk memory proposal] is enabled.

        [bulk memory proposal]: https://github.com/webassembly/bulk-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_bulk_memory_set(self.__ptr__, enable)

    @setter_property
    def wasm_multi_value(self, enable):
        """
        Configures whether the wasm [multi value proposal] is enabled.

        [multi value proposal]: https://github.com/webassembly/multi-value
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_multi_value_set(self.__ptr__, enable)

    @setter_property
    def strategy(self, strategy):
        """
        Configures the compilation strategy used for wasm code.

        Acceptable values for `strategy` are:

        * `"auto"`
        * `"cranelift"`
        * `"lightbeam"`
        """

        if strategy == "auto":
            error = dll.wasmtime_config_strategy_set(self.__ptr__, 0)
        elif strategy == "cranelift":
            error = dll.wasmtime_config_strategy_set(self.__ptr__, 1)
        elif strategy == "lightbeam":
            error = dll.wasmtime_config_strategy_set(self.__ptr__, 2)
        else:
            raise WasmtimeError("unknown strategy: " + str(strategy))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @setter_property
    def cranelift_debug_verifier(self, enable):
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_cranelift_debug_verifier_set(self.__ptr__, enable)

    @setter_property
    def cranelift_opt_level(self, opt_level):
        if opt_level == "none":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 0)
        elif opt_level == "speed":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 1)
        elif opt_level == "speed_and_size":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 2)
        else:
            raise WasmtimeError("unknown opt level: " + str(opt_level))

    @setter_property
    def profiler(self, profiler):
        if profiler == "none":
            error = dll.wasmtime_config_profiler_set(self.__ptr__, 0)
        elif profiler == "jitdump":
            error = dll.wasmtime_config_profiler_set(self.__ptr__, 1)
        else:
            raise WasmtimeError("unknown profiler: " + str(profiler))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @setter_property
    def cache(self, enabled):
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
            error = dll.wasmtime_config_cache_config_load(self.__ptr__, 0)
        elif isinstance(enabled, str):
            error = dll.wasmtime_config_cache_config_load(self.__ptr__,
                                                          c_char_p(enabled.encode('utf-8')))
        else:
            raise TypeError("expected string or bool")
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @setter_property
    def interruptable(self, enabled):
        """
        Configures whether wasm execution can be interrupted via interrupt
        handles.
        """

        if enabled:
            val = 1
        else:
            val = 0
        dll.wasmtime_config_interruptable_set(self.__ptr__, val)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_config_delete(self.__ptr__)
