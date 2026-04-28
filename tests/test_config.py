import unittest
from contextlib import closing

from wasmtime import *


class TestConfig(unittest.TestCase):
    def test_smoke(self):
        config = Config()
        config.debug_info = True
        config.wasm_threads = True
        config.wasm_tail_call = True
        config.wasm_reference_types = True
        config.wasm_simd = True
        config.wasm_bulk_memory = True
        config.wasm_multi_value = True
        config.wasm_multi_memory = True
        config.wasm_memory64 = True
        config.wasm_exceptions = True
        config.wasm_component_model = True
        config.wasm_component_model_map = True
        config.wasm_function_references = True
        config.wasm_wide_arithmetic = True
        config.wasm_custom_page_sizes = True
        config.wasm_gc = True
        config.wasm_stack_switching = True
        config.wasm_relaxed_simd = True
        config.wasm_relaxed_simd_deterministic = True

        config.strategy = "cranelift"
        config.strategy = "auto"
        config.cache = True
        config.parallel_compilation = False
        with self.assertRaises(WasmtimeError):
            config.cache = "./test.toml"
        with self.assertRaises(WasmtimeError):
            config.strategy = "nonexistent-strategy"
        config.cranelift_opt_level = "none"
        config.cranelift_opt_level = "speed_and_size"
        config.cranelift_opt_level = "speed"
        with self.assertRaises(WasmtimeError):
            config.cranelift_opt_level = "nonexistent-level"
        config.profiler = "none"
        config.profiler = "jitdump"
        config.profiler = "vtune"
        config.profiler = "perfmap"
        with self.assertRaises(WasmtimeError):
            config.profiler = "nonexistent-profiler"

        config.cranelift_debug_verifier = True
        config.cranelift_nan_canonicalization = True
        config.cranelift_flag_enable("preserve_frame_pointers")
        config.cranelift_flag_set("opt_level", "speed")

        config.consume_fuel = True
        config.max_wasm_stack = 1024 * 1024
        config.gc_support = True
        config.native_unwind_info = True
        config.macos_use_mach_ports = True
        config.signals_based_traps = True

        config.memory_may_move = True
        config.memory_reservation = 1 << 20
        config.memory_guard_size = 1 << 16
        config.memory_reservation_for_growth = 1 << 20
        config.memory_init_cow = True

    def test_target(self):
        config = Config()
        # Setting the host target should always succeed
        import platform
        host_triple = None
        if platform.machine() == "x86_64" and platform.system() == "Linux":
            host_triple = "x86_64-unknown-linux-gnu"
        elif platform.machine() == "aarch64" and platform.system() == "Linux":
            host_triple = "aarch64-unknown-linux-gnu"
        if host_triple is not None:
            config.target = host_triple
        # An invalid target should raise
        with self.assertRaises(WasmtimeError):
            config.target = "not-a-real-target"

        with closing(config) as config:
            pass

        config.close()

        with self.assertRaises(ValueError):
            Engine(config)

        with self.assertRaises(ValueError):
            config.cache = True
