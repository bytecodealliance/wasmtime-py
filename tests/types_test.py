import unittest

from wasmtime import FuncType, ValType

class TestTypes(unittest.TestCase):
    def test_valtypes(self):
        i32 = ValType.i32()
        i64 = ValType.i64()
        f32 = ValType.f32()
        f64 = ValType.f64()

    def test_new(self):
        ty = FuncType([], [])
        ty = FuncType([ValType.i32()], [ValType.i64()])
