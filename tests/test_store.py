import unittest

from wasmtime import *


class TestStore(unittest.TestCase):
    def test_smoke(self):
        Store()
        Store(Engine())

    def test_errors(self):
        with self.assertRaises(TypeError):
            Store(3)  # type: ignore

    def test_interrupt_handle_requires_interruptable(self):
        with self.assertRaises(WasmtimeError):
            Store().interrupt_handle()

    def test_interrupt_handle(self):
        config = Config()
        config.interruptable = True
        store = Store(Engine(config))
        store.interrupt_handle().interrupt()

    def test_interrupt_wasm(self):
        config = Config()
        config.interruptable = True
        store = Store(Engine(config))
        interrupt_handle = store.interrupt_handle()

        module = Module(store, """
            (import "" "" (func))
            (func
                call 0
                (loop br 0))
            (start 1)
        """)
        interrupt = Func(store, FuncType([], []), lambda: interrupt_handle.interrupt())
        with self.assertRaises(Trap):
            Instance(store, module, [interrupt])
