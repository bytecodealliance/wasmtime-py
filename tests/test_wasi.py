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

    def test_custom_print(self):
        linker = Linker(Engine())
        linker.define_wasi()

        stderr = ''
        stdout = ''

        def on_stdout(data: bytes) -> None:
            nonlocal stdout
            stdout += data.decode('utf8')

        def on_stderr(data: bytes) -> None:
            nonlocal stderr
            stderr += data.decode('utf8')

        module = Module(linker.engine, """
            (module
                (import "wasi_snapshot_preview1" "fd_write"
                    (func $write (param i32 i32 i32 i32) (result i32)))

                (memory (export "memory") 1)

                (func $print
                    (i32.store (i32.const 300) (i32.const 100)) ;; iov base
                    (i32.store (i32.const 304) (i32.const 14))  ;; iov len

                    (call $write
                        (i32.const 1)    ;; fd 1 is stdout
                        (i32.const 300)  ;; iovecs ptr
                        (i32.const 1)    ;; iovecs len
                        (i32.const 400)) ;; nwritten ptr
                    if unreachable end   ;; verify no error

                    (i32.store (i32.const 300) (i32.const 200)) ;; iov base
                    (i32.store (i32.const 304) (i32.const 14))  ;; iov len

                    (call $write
                        (i32.const 2)    ;; fd 2 is stderr
                        (i32.const 300)  ;; iovecs ptr
                        (i32.const 1)    ;; iovecs len
                        (i32.const 400)) ;; nwritten ptr
                    if unreachable end   ;; verify no error
                )

                (start $print)

                (data (i32.const 100) "Hello, stdout!")
                (data (i32.const 200) "Hello, stderr!")
            )
        """)

        wasi = WasiConfig()
        wasi.stdout_custom = on_stdout
        wasi.stderr_custom = on_stderr

        store = Store(linker.engine)
        store.set_wasi(wasi)
        linker.instantiate(store, module)

        self.assertEqual('Hello, stdout!', stdout)
        self.assertEqual('Hello, stderr!', stderr)
