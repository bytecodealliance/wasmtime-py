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

    def test_slices(self):
        store = Store()
        ty = MemoryType(Limits(1, None))
        memory = Memory(store, ty)
        memory.grow(store, 2)
        data_ptr = memory.data_ptr(store)
        ba = bytearray([i for i in range(200)])
        size_bytes = memory.data_len(store)
        # happy cases
        offset = 2048
        ba_size = len(ba)
        # write with start and ommit stop
        memory.write(store, ba, offset)
        out = memory.read(store, offset, offset + ba_size)
        self.assertEqual(ba, out)
        self.assertEqual(data_ptr[offset], 0)
        self.assertEqual(data_ptr[offset + 1], 1)
        self.assertEqual(data_ptr[offset + 199], 199)
        self.assertEqual(len(memory.read(store, -10)), 10)
        # write with start and stop
        memory.write(store, ba, offset + ba_size)
        out = memory.read(store, offset + ba_size, offset + ba_size + ba_size)
        self.assertEqual(ba, out)
        # assert old
        self.assertEqual(data_ptr[offset], 0)
        self.assertEqual(data_ptr[offset + 1], 1)
        self.assertEqual(data_ptr[offset + 199], 199)
        # assert new
        self.assertEqual(data_ptr[offset + ba_size], 0)
        self.assertEqual(data_ptr[offset + ba_size + 1], 1)
        self.assertEqual(data_ptr[offset + ba_size + 199], 199)
        # edge cases
        # empty slices
        self.assertEqual(len(memory.read(store, 0, 0)), 0)
        self.assertEqual(len(memory.read(store, offset, offset)), 0)
        self.assertEqual(len(memory.read(store, offset, offset - 1)), 0)
        # out of bound access returns empty array similar to list slice
        self.assertEqual(len(memory.read(store, size_bytes + 1)), 0)
        # write empty
        self.assertEqual(memory.write(store, bytearray(0), offset), 0)
        self.assertEqual(memory.write(store, bytearray(b""), offset), 0)
        with self.assertRaises(IndexError):
            memory.write(store, ba, size_bytes)
        with self.assertRaises(IndexError):
            memory.write(store, ba, size_bytes-ba_size+1)
        self.assertEqual(memory.write(store, ba, -ba_size), ba_size)
        out = memory.read(store, -ba_size)
        self.assertEqual(ba, out)
