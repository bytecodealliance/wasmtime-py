import unittest

from wasmtime import *


class TestConfig(unittest.TestCase):
    def test_smoke(self):
        config = Config()
        config.debug_info(True)
        config.wasm_threads(True)
        config.wasm_reference_types(True)
        config.wasm_simd(True)
        config.wasm_bulk_memory(True)
        config.wasm_multi_value(True)
        config.cranelift_debug_verifier(True)
        config.strategy("cranelift")
        config.strategy("auto")
        try:
            config.strategy("lightbeam")
        except RuntimeError:
            pass  # this may fail to be enabled
        with self.assertRaises(RuntimeError):
            config.strategy("nonexistent-strategy")
        config.cranelift_opt_level("none")
        config.cranelift_opt_level("speed_and_size")
        config.cranelift_opt_level("speed")
        with self.assertRaises(RuntimeError):
            config.cranelift_opt_level("nonexistent-level")
        config.profiler("none")
        with self.assertRaises(RuntimeError):
            config.profiler("nonexistent-profiler")
