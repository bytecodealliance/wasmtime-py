import unittest

from wasmtime import *


class TestSharedMemory(unittest.TestCase):
    def test_new(self):
        engine = Store().engine
        memory_type = MemoryType(Limits(1, 2), is_64=False, shared=True)
        assert(not memory_type.is_64)
        shared_memory = SharedMemory(engine, memory_type)
        with self.assertRaises(TypeError):
            shared_memory.grow('')  # type: ignore
        with self.assertRaises(WasmtimeError):
            shared_memory.grow(-1)
        self.assertEqual(shared_memory.data_ptr()[0], 0)
        self.assertEqual(shared_memory.data_len(), 65536)
        self.assertTrue(isinstance(shared_memory.type(), MemoryType))

    def test_grow(self):
        engine = Store().engine
        memory_type = MemoryType(Limits(1, 2), shared=True)
        shared_memory = SharedMemory(engine, memory_type)
        assert(shared_memory.grow(1) == 1)
        assert(shared_memory.grow(0) == 2)
        with self.assertRaises(WasmtimeError):
            shared_memory.grow(1)

    def test_errors(self):
        engine = Store().engine
        ty = MemoryType(Limits(1, 2), shared=True)
        with self.assertRaises(AttributeError):
            SharedMemory(1, ty)  # type: ignore
        with self.assertRaises(AttributeError):
            SharedMemory(engine, 1)  # type: ignore

    def test_shared_memory_type_fails_if_no_max_specified(self):
        with self.assertRaises(WasmtimeError):
            # Shared memories must have a max size
            MemoryType(Limits(0x100000000, None), shared=True)

    def test_shared_memory_type_works_if_min_max_i64_is_set(self):
        ty = MemoryType(Limits(0x100000000, 0x100000000), is_64=True, shared=True)
        assert(ty.limits.min == 0x100000000)
        assert(ty.limits.max == 0x100000000)
        assert(ty.is_64)
        
    def test_shared_memory_type_fails_if_is_too_large(self):
        with self.assertRaises(WasmtimeError):
            MemoryType(Limits(1, 0x100000000), shared=True)

    def test_memory_type_has_to_be_shared(self):
        engine = Store().engine
        ty = MemoryType(Limits(1, 2))
        with self.assertRaises(WasmtimeError):
            SharedMemory(engine, ty)
