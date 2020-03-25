import unittest

from wasmtime import *


class TestValue(unittest.TestCase):
    def test_i32(self):
        with self.assertRaises(TypeError):
            Val.i32('')
        with self.assertRaises(TypeError):
            Val.i32(1.2)

        i = Val.i32(1)
        self.assertEqual(i.get_i32(), 1)
        i = Val.i32(0xffffffff)
        self.assertEqual(i.get_i32(), -1)
        i = Val.i32(0x800000000)
        self.assertEqual(i.get_i32(), 0)

        self.assertEqual(None, i.get_i64())
        self.assertEqual(None, i.get_f32())
        self.assertEqual(None, i.get_f64())
        self.assertEqual(i.type(), ValType.i32())

    def test_i64(self):
        with self.assertRaises(TypeError):
            Val.i64('')
        with self.assertRaises(TypeError):
            Val.i64(1.2)

        i = Val.i64(1)
        self.assertEqual(i.get_i64(), 1)
        i = Val.i64(0xffffffff)
        self.assertEqual(i.get_i64(), 0xffffffff)
        i = Val.i64(0x800000000)
        self.assertEqual(i.get_i64(), 0x800000000)
        i = Val.i64(0xffffffffffffffff)
        self.assertEqual(i.get_i64(), -1)
        i = Val.i64(0x80000000000000000)
        self.assertEqual(i.get_i64(), 0)

        self.assertEqual(None, i.get_i32())
        self.assertEqual(None, i.get_f32())
        self.assertEqual(None, i.get_f64())
        self.assertEqual(i.type(), ValType.i64())

    def test_f32(self):
        with self.assertRaises(TypeError):
            Val.f32('')
        with self.assertRaises(TypeError):
            Val.f32(1)

        i = Val.f32(1.0)
        self.assertEqual(i.get_f32(), 1.0)
        self.assertEqual(None, i.get_i64())
        self.assertEqual(None, i.get_i32())
        self.assertEqual(None, i.get_f64())
        self.assertEqual(i.type(), ValType.f32())

    def test_f64(self):
        with self.assertRaises(TypeError):
            Val.f64('')
        with self.assertRaises(TypeError):
            Val.f64(1)

        i = Val.f64(1.0)
        self.assertEqual(i.get_f64(), 1.0)
        self.assertEqual(None, i.get_i32())
        self.assertEqual(None, i.get_i64())
        self.assertEqual(None, i.get_f32())
        self.assertEqual(i.type(), ValType.f64())
