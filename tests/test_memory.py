import unittest

from wasmtime import *


class TestMemory(unittest.TestCase):
    def test_new(self):
        store = Store()
        ty = MemoryType(Limits(1, None))
        memory = Memory(store, ty)
        self.assertEqual(memory.type().limits(), Limits(1, None))
        self.assertEqual(memory.size(), 1)
        self.assertTrue(memory.grow(1))
        self.assertEqual(memory.size(), 2)
        self.assertTrue(memory.grow(0))
        self.assertEqual(memory.size(), 2)
        with self.assertRaises(TypeError):
            memory.grow('')
        with self.assertRaises(RuntimeError):
            memory.grow(-1)
        self.assertEqual(memory.data_ptr()[0], 0)
        self.assertEqual(memory.data_len(), 65536 * 2)
        self.assertTrue(memory.as_extern().type().memory_type() is not None)
        self.assertTrue(memory.as_extern().type().global_type() is None)
        self.assertTrue(memory.as_extern().type().func_type() is None)
        self.assertTrue(memory.as_extern().type().table_type() is None)

    def test_grow(self):
        store = Store()
        ty = MemoryType(Limits(1, 2))
        memory = Memory(store, ty)
        self.assertTrue(memory.grow(1))
        self.assertTrue(memory.grow(0))
        self.assertFalse(memory.grow(1))

    def test_errors(self):
        store = Store()
        ty = MemoryType(Limits(1, 2))
        with self.assertRaises(TypeError):
            Memory(1, ty)
        with self.assertRaises(TypeError):
            Memory(store, 1)
