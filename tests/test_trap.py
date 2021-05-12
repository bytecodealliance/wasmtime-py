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
        try:
            e = i.exports(store)[0]
            assert(isinstance(e, Func))
            e(store)
        except Trap as e:
            trap = e

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
wasm trap: unreachable
wasm backtrace:
    0:   0x2d - module!bar
    1:   0x28 - module!foo
    2:   0x23 - module!<wasm function 0>
""")

    def test_frames_no_module(self):
        store = Store()
        module = Module(store.engine, """
            (module
                (func (export "init") unreachable)
            )
        """)
        i = Instance(store, module, [])
        try:
            e = i.exports(store)[0]
            assert(isinstance(e, Func))
            e(store)
        except Trap as e:
            trap = e

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

        try:
            exit(store, 0)
            assert(False)
        except ExitTrap as e:
            assert(e.code == 0)

        try:
            exit(store, 1)
            assert(False)
        except ExitTrap as e:
            assert(e.code == 1)
