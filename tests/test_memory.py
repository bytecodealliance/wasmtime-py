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
        ba = bytearray([i for i in range(200)])
        size_bytes = memory.data_len(store)
        slicer = memory.get_slicer(store)
        # out of bound access
        with self.assertRaises(IndexError):
            _ = slicer[size_bytes + 1]
        # out of bound set
        with self.assertRaises(IndexError):
            slicer[size_bytes + 1] = 0
        # non-slice key read/write
        with self.assertRaises(TypeError):
            _ = slicer[(1, 2)]  # type: ignore
        with self.assertRaises(TypeError):
            _ = slicer["foo"]  # type: ignore
        with self.assertRaises(TypeError):
            slicer[(1, 2)] = ba  # type: ignore
        with self.assertRaises(TypeError):
            slicer["foo"] = ba  # type: ignore
        # slice with step
        with self.assertRaises(ValueError):
            _ = slicer[1:100:2]
        with self.assertRaises(ValueError):
            slicer[1:100:2] = ba
        offset = 2048
        ba_size = len(ba)
        slicer[offset:] = ba
        out = slicer[offset: offset + ba_size]
        self.assertEqual(ba, out)
        self.assertEqual(slicer[offset + 199], 199)
        self.assertEqual(len(slicer[-10:]), 10)
        self.assertEqual(len(slicer[offset:offset]), 0)
        self.assertEqual(len(slicer[offset: offset - 1]), 0)
        slicer[offset + ba_size: offset + ba_size + ba_size] = ba
        out = slicer[offset: offset + ba_size]
        self.assertEqual(ba, out)
        self.assertEqual(slicer[offset + ba_size + 199], 199)
