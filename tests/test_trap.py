import unittest

from wasmtime import *


class TestTrap(unittest.TestCase):
    def test_new(self):
        trap = Trap('x')
        self.assertEqual(trap.message, u'x')

    def test_frames(self):
        store = Store()
        module = Module(store.engine, """
            (module $module
                (func (export "init")
                    call $foo)
                (func $foo
                    call $bar)
                (func $bar
                    unreachable)
            )
        """)
        i = Instance(store, module, [])
        with self.assertRaises(Trap) as exn:
            e = i.exports(store).by_index[0]
            assert(isinstance(e, Func))
            e(store)
        trap = exn.exception

        frames = trap.frames
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0].func_index, 2)
        self.assertEqual(frames[1].func_index, 1)
        self.assertEqual(frames[2].func_index, 0)

        self.assertEqual(frames[0].func_name, 'bar')
        self.assertEqual(frames[1].func_name, 'foo')
        self.assertEqual(frames[2].func_name, None)

        self.assertEqual(frames[0].module_name, 'module')
        self.assertEqual(frames[1].module_name, 'module')
        self.assertEqual(frames[2].module_name, 'module')

        self.assertEqual(str(trap), """\
error while executing at wasm backtrace:
    0:     0x2d - module!bar
    1:     0x28 - module!foo
    2:     0x23 - module!<wasm function 0>

Caused by:
    wasm trap: wasm `unreachable` instruction executed\
""")
        self.assertEqual(trap.trap_code, TrapCode.UNREACHABLE)

    def test_frames_no_module(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (func (export "init") unreachable)
            )
        """)
        i = Instance(store, module, [])
        with self.assertRaises(Trap) as exn:
            e = i.exports(store).by_index[0]
            assert(isinstance(e, Func))
            e(store)
        trap = exn.exception

        frames = trap.frames
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].func_index, 0)
        self.assertEqual(frames[0].func_name, None)
        self.assertEqual(frames[0].module_name, None)

    def test_wasi_exit(self):
        linker = Linker(Engine())
        linker.define_wasi()
        module = Module(linker.engine, """
            (module
                (import "wasi_snapshot_preview1" "proc_exit" (func $exit (param i32)))
                (memory (export "memory") 1)
                (func (export "exit") (param i32)
                    local.get 0
                    call $exit)
            )
        """)
        store = Store(linker.engine)
        store.set_wasi(WasiConfig())
        instance = linker.instantiate(store, module)
        exit = instance.exports(store)["exit"]
        assert(isinstance(exit, Func))

        with self.assertRaises(ExitTrap) as exn:
            exit(store, 0)
        self.assertEqual(exn.exception.code, 0)
        self.assertRegex(str(exn.exception), 'Exited with i32 exit status 0')

        with self.assertRaises(ExitTrap) as exn:
            exit(store, 1)
        self.assertEqual(exn.exception.code, 1)
