from ._ffi import *
from ctypes import *
from wasmtime import WasmtimeError

dll.wasm_config_new.restype = P_wasm_config_t
dll.wasmtime_config_strategy_set.restype = P_wasmtime_error_t
dll.wasmtime_config_profiler_set.restype = P_wasmtime_error_t


class Config(object):
    """
    Global configuration, used to create an `Engine`.

    A `Config` houses a number of configuration options which tweaks how wasm
    code is compiled or generated.
    """

    def __init__(self):
        self.__ptr__ = dll.wasm_config_new()

    def debug_info(self, enable):
        """
        Configures whether DWARF debug information is emitted for the generated
        code. This can improve profiling and the debugging experience.
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_debug_info_set(self.__ptr__, enable)

    def wasm_threads(self, enable):
        """
        Configures whether the wasm [threads proposal] is enabled.

        [threads proposal]: https://github.com/webassembly/threads
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_threads_set(self.__ptr__, enable)

    def wasm_reference_types(self, enable):
        """
        Configures whether the wasm [reference types proposal] is enabled.

        [reference types proposal]: https://github.com/webassembly/reference-types
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_reference_types_set(self.__ptr__, enable)

    def wasm_simd(self, enable):
        """
        Configures whether the wasm [SIMD proposal] is enabled.

        [SIMD proposal]: https://github.com/webassembly/simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_simd_set(self.__ptr__, enable)

    def wasm_bulk_memory(self, enable):
        """
        Configures whether the wasm [bulk memory proposal] is enabled.

        [bulk memory proposal]: https://github.com/webassembly/bulk-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_bulk_memory_set(self.__ptr__, enable)

    def wasm_multi_value(self, enable):
        """
        Configures whether the wasm [multi value proposal] is enabled.

        [multi value proposal]: https://github.com/webassembly/multi-value
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_wasm_multi_value_set(self.__ptr__, enable)

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

    def cranelift_debug_verifier(self, enable):
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        dll.wasmtime_config_cranelift_debug_verifier_set(self.__ptr__, enable)

    def cranelift_opt_level(self, opt_level):
        if opt_level == "none":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 0)
        elif opt_level == "speed":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 1)
        elif opt_level == "speed_and_size":
            dll.wasmtime_config_cranelift_opt_level_set(self.__ptr__, 2)
        else:
            raise WasmtimeError("unknown opt level: " + str(opt_level))

    def profiler(self, profiler):
        if profiler == "none":
            error = dll.wasmtime_config_profiler_set(self.__ptr__, 0)
        elif profiler == "jitdump":
            error = dll.wasmtime_config_profiler_set(self.__ptr__, 1)
        else:
            raise WasmtimeError("unknown profiler: " + str(profiler))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_config_delete(self.__ptr__)
