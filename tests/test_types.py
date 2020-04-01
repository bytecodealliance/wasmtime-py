import unittest

from wasmtime import FuncType, ValType


class TestTypes(unittest.TestCase):
    def test_valtypes(self):
        ValType.i32()
        ValType.i64()
        ValType.f32()
        ValType.f64()

    def test_new(self):
        FuncType([], [])
        FuncType([ValType.i32()], [ValType.i64()])
