import unittest

from wasmtime import *


class TestMemory(unittest.TestCase):
    def test_new(self):
        store = Store()
        ty = MemoryType(Limits(1, None))
        memory = Memory(store, ty)
        self.assertEqual(memory.type(store).limits, Limits(1, None))
        self.assertEqual(memory.size(store), 1)
        self.assertTrue(memory.grow(store, 1))
        self.assertEqual(memory.size(store), 2)
        self.assertTrue(memory.grow(store, 0))
        self.assertEqual(memory.size(store), 2)
        with self.assertRaises(TypeError):
            memory.grow(store, '')  # type: ignore
        with self.assertRaises(WasmtimeError):
            memory.grow(store, -1)
        self.assertEqual(memory.data_ptr(store)[0], 0)
        self.assertEqual(memory.data_len(store), 65536 * 2)
        self.assertTrue(isinstance(memory.type(store), MemoryType))

    def test_grow(self):
        store = Store()
        ty = MemoryType(Limits(1, 2))
        memory = Memory(store, ty)
        assert(memory.grow(store, 1) == 1)
        assert(memory.grow(store, 0) == 2)
        with self.assertRaises(WasmtimeError):
            memory.grow(store, 1)

    def test_errors(self):
        store = Store()
        ty = MemoryType(Limits(1, 2))
        with self.assertRaises(AttributeError):
            Memory(1, ty)  # type: ignore
        with self.assertRaises(AttributeError):
            Memory(store, 1)  # type: ignore
