import unittest
import tempfile

from wasmtime import *


class TestWasi(unittest.TestCase):
    def test_config(self):
        config = WasiConfig()
        config.argv = ['a', 'b']
        config.inherit_argv()
        config.env = [['a', 'b']]
        config.inherit_env()

        with tempfile.NamedTemporaryFile() as f:
            config.stdin_file = f.name
            config.inherit_stdin()
            config.stdout_file = f.name
            config.inherit_stdout()
            config.stderr_file = f.name
            config.inherit_stderr()
        config.preopen_dir('wasmtime', 'other')

    def test_instance(self):
        config = WasiConfig()
        instance = WasiInstance(Store(), "wasi_unstable", config)

        # specify nonexistent version
        with self.assertRaises(Trap):
            WasiInstance(Store(), "nonexistent_wasi", WasiConfig())
        # re-use config
        with self.assertRaises(AttributeError):
            WasiInstance(Store(), "nonexistent_wasi", config)

        # Type errors
        with self.assertRaises(TypeError):
            WasiInstance(1, "nonexistent_wasi", config)
        with self.assertRaises(TypeError):
            WasiInstance(Store(), 1, config)
        with self.assertRaises(TypeError):
            WasiInstance(Store(), "nonexistent_wasi", 1)
        with self.assertRaises(TypeError):
            instance.bind(3)

        module = Module(instance.store, """
            (module
                (import "wasi_unstable" "random_get"
                    (func (param i32 i32) (result i32)))
            )
        """)
        imp = module.imports[0]
        binding = instance.bind(imp)
        self.assertTrue(isinstance(binding, Func))
        binding(1, 2)  # should return EFAULT basically

    def test_preview1(self):
        config = WasiConfig()
        instance = WasiInstance(Store(), "wasi_snapshot_preview1", config)

        module = Module(instance.store, """
            (module
                (import "wasi_snapshot_preview1" "random_get"
                    (func (param i32 i32) (result i32)))
            )
        """)
        imp = module.imports[0]
        binding = instance.bind(imp)
        self.assertTrue(isinstance(binding, Func))
        binding(1, 2)  # should return EFAULT basically
