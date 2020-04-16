import unittest

from wasmtime import *


class TestTrap(unittest.TestCase):
    def test_new(self):
        store = Store()
        trap = Trap(store, 'x')
        self.assertEqual(trap.message(), u'x')

    def test_errors(self):
        store = Store()
        with self.assertRaises(TypeError):
            Trap(1, '')
        with self.assertRaises(TypeError):
            Trap(store, 1)

    def test_frames(self):
        store = Store()
        module = Module(store, """
            (module $module
                (func (export "init")
                    call $foo)
                (func $foo
                    call $bar)
                (func $bar
                    unreachable)
            )
        """)
        i = Instance(module, [])
        try:
            i.exports()[0].func().call()
        except Trap as e:
            trap = e

        frames = trap.frames()
        self.assertEqual(len(frames), 3)
        self.assertEqual(frames[0].func_index(), 2)
        self.assertEqual(frames[1].func_index(), 1)
        self.assertEqual(frames[2].func_index(), 0)

        self.assertEqual(frames[0].func_name(), 'bar')
        self.assertEqual(frames[1].func_name(), 'foo')
        self.assertEqual(frames[2].func_name(), None)

        self.assertEqual(frames[0].module_name(), 'module')
        self.assertEqual(frames[1].module_name(), 'module')
        self.assertEqual(frames[2].module_name(), 'module')

        self.assertEqual(str(trap), """\
wasm trap: unreachable
wasm backtrace:
  0:   0x2d - module!bar
  1:   0x28 - module!foo
  2:   0x23 - module!<wasm function 0>
""")

    def test_frames_no_module(self):
        store = Store()
        module = Module(store, """
            (module
                (func (export "init") unreachable)
            )
        """)
        i = Instance(module, [])
        try:
            i.exports()[0].func().call()
        except Trap as e:
            trap = e

        frames = trap.frames()
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].func_index(), 0)
        self.assertEqual(frames[0].func_name(), None)
        self.assertEqual(frames[0].module_name(), None)
