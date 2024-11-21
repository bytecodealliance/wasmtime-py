import unittest
import tempfile

from wasmtime import *
from pathlib import Path


class TestWasi(unittest.TestCase):
    def test_config(self):
        config = WasiConfig()
        config.argv = ['a', 'b']
        config.inherit_argv()
        config.env = [['a', 'b']]
        config.inherit_env()

        with tempfile.NamedTemporaryFile() as f:
            config.stdin_file = f.name
            config.stdin_file = Path(f.name)
            config.inherit_stdin()
            config.stdout_file = f.name
            config.stdout_file = Path(f.name)
            config.inherit_stdout()
            config.stderr_file = f.name
            config.stderr_file = Path(f.name)
            config.inherit_stderr()

        with self.assertRaises(WasmtimeError):
            config.stdin_file = 'somewhere-over-the-rainboat'
        with self.assertRaises(WasmtimeError):
            config.stdout_file = 'some-directory/without-a-rainbow'
        with self.assertRaises(WasmtimeError):
            config.stderr_file = 'some-directory/without-a-rainbow'
        config.preopen_dir('wasmtime', 'other', DirPerms.READ_WRITE, FilePerms.READ_WRITE)
        config.preopen_dir('wasmtime', 'other2')

    def test_preview1(self):
        linker = Linker(Engine())
        linker.define_wasi()

        module = Module(linker.engine, """
            (module
                (import "wasi_snapshot_preview1" "random_get"
                    (func (param i32 i32) (result i32)))
            )
        """)

        store = Store(linker.engine)
        store.set_wasi(WasiConfig())
        linker.instantiate(store, module)

    def preopen_nonexistent(self):
        config = WasiConfig()
        with self.assertRaises(WasmtimeError):
            config.preopen_dir('/path/to/nowhere', '/', DirPerms.READ_ONLY, FilePerms.READ_ONLY)
