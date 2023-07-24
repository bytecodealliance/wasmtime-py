import unittest

from wasmtime import *


class TestStore(unittest.TestCase):
    def test_smoke(self):
        Store()
        Store(Engine())

    def test_errors(self):
        with self.assertRaises(TypeError):
            Store(3)  # type: ignore

    def test_interrupt_handle(self):
        config = Config()
        config.epoch_interruption = True
        engine = Engine(config)
        engine.increment_epoch()
        store = Store(engine)
        store.set_epoch_deadline(1)

    def test_interrupt_wasm(self):
        config = Config()
        config.epoch_interruption = True
        engine = Engine(config)
        store = Store(engine)
        store.set_epoch_deadline(1)

        module = Module(store.engine, """
            (import "" "hit" (func $hit))
            (import "" "interrupt" (func $interrupt))
            (func $start
                call $hit
                call $interrupt
                (loop br 0))
            (start $start)
        """)
        interrupt = Func(store, FuncType([], []), lambda: engine.increment_epoch())

        was_hit = False

        def hit_callback():
            nonlocal was_hit
            was_hit = True
        hit = Func(store, FuncType([], []), hit_callback)

        with self.assertRaises(Trap):
            Instance(store, module, [hit, interrupt])
        self.assertTrue(was_hit)

    def test_fuel(self):
        store = Store()

        with self.assertRaises(WasmtimeError):
            store.add_fuel(1)
        with self.assertRaises(WasmtimeError):
            store.fuel_consumed()

        config = Config()
        config.consume_fuel = True
        store = Store(Engine(config))
        store.add_fuel(1)
        assert(store.fuel_consumed() == 0)
        assert(store.consume_fuel(0) == 1)
        store.add_fuel(1)
        assert(store.consume_fuel(1) == 1)
        with self.assertRaises(WasmtimeError):
            store.consume_fuel(2)

    def test_limits(self):
        store = Store()
        Memory(store, MemoryType(Limits(1, None)))

        store = Store()
        store.set_limits(memory_size=0)
        with self.assertRaises(WasmtimeError):
            Memory(store, MemoryType(Limits(1, None)))
        store.set_limits(memory_size=100000)
        Memory(store, MemoryType(Limits(1, None)))

        store = Store()
        store.set_limits(table_elements=1)
        Table(store, TableType(ValType.funcref(), Limits(1, None)), None)
        with self.assertRaises(WasmtimeError):
            Table(store, TableType(ValType.funcref(), Limits(2, None)), None)

        store = Store()
        store.set_limits(memory_size=200000)
        mem = Memory(store, MemoryType(Limits(1, None)))
        mem.grow(store, 1)
        with self.assertRaises(WasmtimeError):
            mem.grow(store, 100)
