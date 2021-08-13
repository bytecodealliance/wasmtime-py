import unittest

from wasmtime import *


class TestConfig(unittest.TestCase):
    def test_smoke(self):
        config = Config()
        config.debug_info = True
        config.wasm_threads = True
        config.wasm_reference_types = True
        config.wasm_simd = True
        config.wasm_bulk_memory = True
        config.wasm_multi_value = True
        config.wasm_multi_memory = True
        config.wasm_memory64 = True
        config.cranelift_debug_verifier = True
        config.strategy = "cranelift"
        config.strategy = "auto"
        config.cache = True
        with self.assertRaises(WasmtimeError):
            config.cache = "./test.toml"
        try:
            config.strategy = "lightbeam"
        except WasmtimeError:
            pass  # this may fail to be enabled
        with self.assertRaises(WasmtimeError):
            config.strategy = "nonexistent-strategy"
        config.cranelift_opt_level = "none"
        config.cranelift_opt_level = "speed_and_size"
        config.cranelift_opt_level = "speed"
        with self.assertRaises(WasmtimeError):
            config.cranelift_opt_level = "nonexistent-level"
        config.profiler = "none"
        with self.assertRaises(WasmtimeError):
            config.profiler = "nonexistent-profiler"
        config.consume_fuel = True
