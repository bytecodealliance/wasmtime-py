from . import _ffi as ffi
import ctypes
from wasmtime import WasmtimeError, Managed
import typing


def setter_property(fset: typing.Callable) -> property:
    prop = property(fset=fset)
    if fset.__doc__:
        prop.__doc__ = fset.__doc__
        prop.__doc__ += "\n\n        Note that this field can only be set, it cannot be read"
    return prop


class Config(Managed["ctypes._Pointer[ffi.wasm_config_t]"]):
    """
    Global configuration, used to create an `Engine`.

    A `Config` houses a number of configuration options which tweaks how wasm
    code is compiled or generated.
    """

    def __init__(self) -> None:
        self._set_ptr(ffi.wasm_config_new())

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_config_t]") -> None:
        ffi.wasm_config_delete(ptr)

    @setter_property
    def debug_info(self, enable: bool) -> None:
        """
        Configures whether DWARF debug information is emitted for the generated
        code. This can improve profiling and the debugging experience.
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_debug_info_set(self.ptr(), enable)

    @setter_property
    def wasm_threads(self, enable: bool) -> None:
        """
        Configures whether the wasm [threads proposal] is enabled.

        [threads proposal]: https://github.com/webassembly/threads
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_threads_set(self.ptr(), enable)

    @setter_property
    def wasm_tail_call(self, enable: bool) -> None:
        """
        Configures whether the wasm [tail call proposal] is enabled.

        [tail call proposal]: https://github.com/WebAssembly/tail-call
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_tail_call_set(self.ptr(), enable)

    @setter_property
    def wasm_reference_types(self, enable: bool) -> None:
        """
        Configures whether the wasm [reference types proposal] is enabled.

        [reference types proposal]: https://github.com/webassembly/reference-types
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_reference_types_set(self.ptr(), enable)

    @setter_property
    def wasm_simd(self, enable: bool) -> None:
        """
        Configures whether the wasm [SIMD proposal] is enabled.

        [SIMD proposal]: https://github.com/webassembly/simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_simd_set(self.ptr(), enable)

    @setter_property
    def wasm_bulk_memory(self, enable: bool) -> None:
        """
        Configures whether the wasm [bulk memory proposal] is enabled.

        [bulk memory proposal]: https://github.com/webassembly/bulk-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_bulk_memory_set(self.ptr(), enable)

    @setter_property
    def wasm_multi_value(self, enable: bool) -> None:
        """
        Configures whether the wasm [multi value proposal] is enabled.

        [multi value proposal]: https://github.com/webassembly/multi-value
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_multi_value_set(self.ptr(), enable)

    @setter_property
    def wasm_multi_memory(self, enable: bool) -> None:
        """
        Configures whether the wasm [multi memory proposal] is enabled.

        [multi memory proposal]: https://github.com/webassembly/multi-memory
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_multi_memory_set(self.ptr(), enable)

    @setter_property
    def wasm_memory64(self, enable: bool) -> None:
        """
        Configures whether the wasm [memory64 proposal] is enabled.

        [memory64 proposal]: https://github.com/webassembly/memory64
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_memory64_set(self.ptr(), enable)

    @setter_property
    def wasm_relaxed_simd(self, enable: bool) -> None:
        """
        Configures whether the wasm [relaxed simd proposal] is enabled.

        [relaxed simd proposal]: https://github.com/webassembly/relaxed-simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_relaxed_simd_set(self.ptr(), enable)

    @setter_property
    def wasm_relaxed_simd_deterministic(self, enable: bool) -> None:
        """
        Configures whether the wasm [relaxed simd proposal] is deterministic
        in is execution as opposed to having the most optimal implementation for
        the current platform.

        [relaxed simd proposal]: https://github.com/webassembly/relaxed-simd
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_relaxed_simd_deterministic_set(self.ptr(), enable)

    @setter_property
    def wasm_component_model(self, enable: bool) -> None:
        """
        Configures whether the WebAssembly component model proposal is enabled.
        """
        if not isinstance(enable, bool):
            raise TypeError("expected a bool")
        ffi.wasmtime_config_wasm_component_model_set(self.ptr(), enable)

    @setter_property
    def wasm_component_model_map(self, enable: bool) -> None:
        """
        Configures whether the WebAssembly component model map types proposal
        is enabled.
        """
        if not isinstance(enable, bool):
            raise TypeError("expected a bool")
        ffi.wasmtime_config_wasm_component_model_map_set(self.ptr(), enable)

    @setter_property
    def wasm_exceptions(self, enable: bool) -> None:
        """
        Configures whether the wasm [exceptions proposal] is enabled.

        [exceptions proposal]: https://github.com/WebAssembly/exception-handling
        """

        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_exceptions_set(self.ptr(), enable)

    @setter_property
    def wasm_function_references(self, enable: bool) -> None:
        """
        Configures whether the wasm [typed function references proposal] is
        enabled.

        [typed function references proposal]: https://github.com/WebAssembly/function-references
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_function_references_set(self.ptr(), enable)

    @setter_property
    def wasm_gc(self, enable: bool) -> None:
        """
        Configures whether the wasm [GC proposal] is enabled.

        [GC proposal]: https://github.com/WebAssembly/gc
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_gc_set(self.ptr(), enable)

    @setter_property
    def wasm_wide_arithmetic(self, enable: bool) -> None:
        """
        Configures whether the wasm [wide arithmetic proposal] is enabled.

        [wide arithmetic proposal]: https://github.com/WebAssembly/wide-arithmetic
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_wide_arithmetic_set(self.ptr(), enable)

    @setter_property
    def wasm_custom_page_sizes(self, enable: bool) -> None:
        """
        Configures whether the wasm [custom-page-sizes proposal] is enabled.

        [custom-page-sizes proposal]: https://github.com/WebAssembly/custom-page-sizes
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_custom_page_sizes_set(self.ptr(), enable)

    @setter_property
    def wasm_stack_switching(self, enable: bool) -> None:
        """
        Configures whether the wasm [stack switching proposal] is enabled.

        [stack switching proposal]: https://github.com/WebAssembly/stack-switching
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_wasm_stack_switching_set(self.ptr(), enable)

    @setter_property
    def strategy(self, strategy: str) -> None:
        """
        Configures the compilation strategy used for wasm code.

        Acceptable values for `strategy` are:

        * `"auto"`
        * `"cranelift"`
        """

        if strategy == "auto":
            ffi.wasmtime_config_strategy_set(self.ptr(), 0)
        elif strategy == "cranelift":
            ffi.wasmtime_config_strategy_set(self.ptr(), 1)
        else:
            raise WasmtimeError("unknown strategy: " + str(strategy))

    @setter_property
    def cranelift_debug_verifier(self, enable: bool) -> None:
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_cranelift_debug_verifier_set(self.ptr(), enable)

    @setter_property
    def cranelift_opt_level(self, opt_level: str) -> None:
        if opt_level == "none":
            ffi.wasmtime_config_cranelift_opt_level_set(self.ptr(), 0)
        elif opt_level == "speed":
            ffi.wasmtime_config_cranelift_opt_level_set(self.ptr(), 1)
        elif opt_level == "speed_and_size":
            ffi.wasmtime_config_cranelift_opt_level_set(self.ptr(), 2)
        else:
            raise WasmtimeError("unknown opt level: " + str(opt_level))

    @setter_property
    def profiler(self, profiler: str) -> None:
        """
        Configures the profiling strategy used for JIT code.

        Acceptable values for `profiler` are:

        * `"none"`
        * `"jitdump"`
        * `"vtune"`
        * `"perfmap"`
        """
        if profiler == "none":
            ffi.wasmtime_config_profiler_set(self.ptr(), 0)
        elif profiler == "jitdump":
            ffi.wasmtime_config_profiler_set(self.ptr(), 1)
        elif profiler == "vtune":
            ffi.wasmtime_config_profiler_set(self.ptr(), 2)
        elif profiler == "perfmap":
            ffi.wasmtime_config_profiler_set(self.ptr(), 3)
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
            error = ffi.wasmtime_config_cache_config_load(self.ptr(), None)
        elif isinstance(enabled, str):
            error = ffi.wasmtime_config_cache_config_load(self.ptr(),
                ctypes.c_char_p(enabled.encode('utf-8')),
            )
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
        ffi.wasmtime_config_epoch_interruption_set(self.ptr(), val)

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
        ffi.wasmtime_config_consume_fuel_set(self.ptr(), instances)

    @setter_property
    def parallel_compilation(self, enable: bool) -> None:
        """
        Configures whether parallel compilation is enabled for functions
        within a module.

        This is enabled by default.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_parallel_compilation_set(self.ptr(), enable)

    @setter_property
    def shared_memory(self, enable: bool) -> None:
        """
        Configures whether shared memories can be created.

        This is disabled by default.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_shared_memory_set(self.ptr(), enable)

    @setter_property
    def max_wasm_stack(self, size: int) -> None:
        """
        Configures the maximum stack size, in bytes, that JIT code can use.

        This defaults to 2MB. Configuring this can help if you hit stack
        overflow or want to limit wasm stack usage.

        Note that if this limit is set too high then the OS's stack guards may
        be hit which will result in an uncaught segfault. This limit can only
        be set to a size that's smaller than the actual OS stack, and that's not
        something able to be dynamically determined, so it's the responsibility
        of embedders to uphold this invariant.
        """
        if not isinstance(size, int):
            raise TypeError('expected an int')
        ffi.wasmtime_config_max_wasm_stack_set(self.ptr(), size)

    @setter_property
    def gc_support(self, enable: bool) -> None:
        """
        Enables or disables GC support in Wasmtime entirely.

        This defaults to `True`.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_gc_support_set(self.ptr(), enable)

    @setter_property
    def cranelift_nan_canonicalization(self, enable: bool) -> None:
        """
        Configures whether Cranelift should perform a NaN-canonicalization pass.

        This replaces NaNs with a single canonical value for fully deterministic
        WebAssembly execution. Not required by the spec; disabled by default.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_cranelift_nan_canonicalization_set(self.ptr(), enable)

    @setter_property
    def memory_may_move(self, enable: bool) -> None:
        """
        Configures whether `memory_reservation` is the maximal size of linear
        memory (disabling movement) or whether linear memories may be moved to
        a new location when they need to grow.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_memory_may_move_set(self.ptr(), enable)

    @setter_property
    def memory_reservation(self, size: int) -> None:
        """
        Configures the initial memory reservation size, in bytes, for linear
        memories.

        For more information see the Rust documentation at
        https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Config.html#method.memory_reservation
        """
        if not isinstance(size, int):
            raise TypeError('expected an int')
        ffi.wasmtime_config_memory_reservation_set(self.ptr(), size)

    @setter_property
    def memory_guard_size(self, size: int) -> None:
        """
        Configures the guard region size, in bytes, for linear memory.

        For more information see the Rust documentation at
        https://bytecodealliance.github.io/wasmtime/api/wasmtime/struct.Config.html#method.memory_guard_size
        """
        if not isinstance(size, int):
            raise TypeError('expected an int')
        ffi.wasmtime_config_memory_guard_size_set(self.ptr(), size)

    @setter_property
    def memory_reservation_for_growth(self, size: int) -> None:
        """
        Configures the size, in bytes, of extra virtual memory reserved for
        memories to grow into after being relocated.

        For more information see the Rust documentation at
        https://docs.wasmtime.dev/api/wasmtime/struct.Config.html#method.memory_reservation_for_growth
        """
        if not isinstance(size, int):
            raise TypeError('expected an int')
        ffi.wasmtime_config_memory_reservation_for_growth_set(self.ptr(), size)

    @setter_property
    def native_unwind_info(self, enable: bool) -> None:
        """
        Configures whether to generate native unwind information (e.g.
        `.eh_frame` on Linux).

        This defaults to `True`.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_native_unwind_info_set(self.ptr(), enable)

    @setter_property
    def target(self, triple: str) -> None:
        """
        Configures the target triple that this configuration will produce
        machine code for.

        Defaults to the native host. Setting this also disables automatic
        inference of native CPU features.

        Raises a `WasmtimeError` if the target triple is not recognized.

        Note that if this is set to something other than the host then an
        `Engine` created won't be able to run generated code, but it can still
        be used to compile code.
        """
        if not isinstance(triple, str):
            raise TypeError('expected a str')
        error = ffi.wasmtime_config_target_set(self.ptr(),
                                               ctypes.c_char_p(triple.encode('utf-8')))
        if error:
            raise WasmtimeError._from_ptr(error)

    def cranelift_flag_enable(self, flag: str) -> None:
        """
        Enables a target-specific flag in Cranelift.

        This can be used to enable CPU features such as SSE4.2 on x86_64
        hosts. Available flags can be explored with `wasmtime settings`.
        """
        if not isinstance(flag, str):
            raise TypeError('expected a str')
        ffi.wasmtime_config_cranelift_flag_enable(self.ptr(),
                                                  ctypes.c_char_p(flag.encode('utf-8')))

    def cranelift_flag_set(self, key: str, value: str) -> None:
        """
        Sets a target-specific flag in Cranelift to the specified value.

        This can be used to configure CPU features such as SSE4.2 on x86_64
        hosts. Available flags can be explored with `wasmtime settings`.
        """
        if not isinstance(key, str):
            raise TypeError('expected a str for key')
        if not isinstance(value, str):
            raise TypeError('expected a str for value')
        ffi.wasmtime_config_cranelift_flag_set(self.ptr(),
                                               ctypes.c_char_p(key.encode('utf-8')),
                                               ctypes.c_char_p(value.encode('utf-8')))

    @setter_property
    def macos_use_mach_ports(self, enable: bool) -> None:
        """
        Configures whether Mach ports are used for exception handling on macOS
        instead of traditional Unix signal handling.

        This defaults to `True` on macOS.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_macos_use_mach_ports_set(self.ptr(), enable)

    @setter_property
    def signals_based_traps(self, enable: bool) -> None:
        """
        Configures whether signals-based trap handlers are enabled (e.g.
        `SIGILL` and `SIGSEGV` on Unix platforms).

        This defaults to `True`.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_signals_based_traps_set(self.ptr(), enable)

    @setter_property
    def memory_init_cow(self, enable: bool) -> None:
        """
        Configures whether copy-on-write memory-mapped data is used to
        initialize linear memory.

        This can significantly improve instantiation performance. Defaults
        to `True`.
        """
        if not isinstance(enable, bool):
            raise TypeError('expected a bool')
        ffi.wasmtime_config_memory_init_cow_set(self.ptr(), enable)
