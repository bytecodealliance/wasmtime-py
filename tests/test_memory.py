import unittest

from wasmtime import *


class TestMemory(unittest.TestCase):
    def test_new(self):
        store = Store()
        ty = MemoryType(Limits(1, None))
        assert(not ty.is_64)
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

    def test_large(self):
        ty = MemoryType(Limits(0x100000000, None), is_64=True)
        assert(ty.limits.min == 0x100000000)
        assert(ty.limits.max is None)
        assert(ty.is_64)
        ty = MemoryType(Limits(0x100000000, 0x100000000), is_64=True)
        assert(ty.limits.min == 0x100000000)
        assert(ty.limits.max == 0x100000000)

        with self.assertRaises(WasmtimeError):
            MemoryType(Limits(0x100000000, None))
        with self.assertRaises(WasmtimeError):
            MemoryType(Limits(1, 0x100000000))
