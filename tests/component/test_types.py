import unittest

from wasmtime import Engine, FuncType as CoreFuncType, GlobalType, WasmtimeError
from wasmtime.component import *

def simplety(name):
    engine = Engine()
    c = Component(engine, f"""
    (component
      (import "a" (func (result {name})))
    )
    """)
    fty = c.type.imports(engine)['a']
    assert(isinstance(fty, FuncType))
    return fty.result

def namedty(contents):
    engine = Engine()
    c = Component(engine, f"""
    (component
      (type $t' {contents})
      (import "t" (type $t (eq $t')))
      (import "a" (func (result $t)))
    )
    """)
    fty = c.type.imports(engine)['a']
    assert(isinstance(fty, FuncType))
    return fty.result

class TestTypes(unittest.TestCase):
    def test_component(self):
        engine = Engine()
        ty = Component(engine, '(component)').type
        self.assertEqual(len(ty.imports(engine)), 0)
        self.assertEqual(len(ty.exports(engine)), 0)

        ty = Component(engine, """
        (component
          (import "a" (core module $a))
          (export "g" (core module $a))
        )
        """).type
        self.assertEqual(len(ty.imports(engine)), 1)
        self.assertIsInstance(ty.imports(engine)['a'], ModuleType)
        self.assertEqual(len(ty.exports(engine)), 1)
        self.assertIsInstance(ty.exports(engine)['g'], ModuleType)

        with self.assertRaises(WasmtimeError):
            ComponentType()

    def test_module(self):
        engine = Engine()
        c = Component(engine, """
        (component
          (import "a" (core module $a
            (import "b" "c" (func))
            (export "d" (global i32))
          ))
        )
        """)
        mty = c.type.imports(engine)['a']
        assert(isinstance(mty, ModuleType))
        imports = mty.imports(engine)
        self.assertEqual(len(imports), 1)
        exports = mty.exports(engine)
        self.assertEqual(len(exports), 1)

        self.assertEqual(imports[0].module, 'b')
        self.assertEqual(imports[0].name, 'c')
        self.assertIsInstance(imports[0].type, CoreFuncType)

        self.assertEqual(exports[0].name, 'd')
        self.assertIsInstance(exports[0].type, GlobalType)

        with self.assertRaises(WasmtimeError):
            ModuleType()

    def test_resource(self):
        engine = Engine()
        c = Component(engine, """
        (component
          (import "a" (type $t (sub resource)))
          (export "a" (type $t))
          (type $t2 (resource (rep i32)))
          (export "b" (type $t2))
        )
        """)
        a1 = c.type.imports(engine)['a']
        a2 = c.type.exports(engine)['a']
        b = c.type.exports(engine)['b']
        assert(isinstance(a1, ResourceType))
        assert(isinstance(a2, ResourceType))
        assert(isinstance(b, ResourceType))
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, b)
        self.assertNotEqual(a2, b)
        self.assertNotEqual(a2, 'hello')

        with self.assertRaises(WasmtimeError):
            ResourceType()

    def test_instance(self):
        engine = Engine()
        cty = Component(engine, """
        (component
          (import "a" (instance
            (export "a" (func))
            (export "b" (core module))
          ))
          (import "b" (instance))
        )
        """).type
        a = cty.imports(engine)['a']
        b = cty.imports(engine)['b']
        assert(isinstance(a, ComponentInstanceType))
        assert(isinstance(b, ComponentInstanceType))
        exports = a.exports(engine)
        self.assertEqual(len(exports), 2)
        self.assertIsInstance(exports['a'], FuncType)
        self.assertIsInstance(exports['b'], ModuleType)

        self.assertEqual(len(b.exports(engine)), 0)

        with self.assertRaises(WasmtimeError):
            ComponentInstanceType()

    def test_func(self):
        engine = Engine()
        cty = Component(engine, """
        (component
          (import "a" (func))
          (import "b" (func (param "x" u32)))
          (import "c" (func (result string)))
          (import "d" (func (param "a" u8) (param "b" u16) (result u32)))
        )
        """).type
        a = cty.imports(engine)['a']
        b = cty.imports(engine)['b']
        c = cty.imports(engine)['c']
        d = cty.imports(engine)['d']
        assert(isinstance(a, FuncType))
        assert(isinstance(b, FuncType))
        assert(isinstance(c, FuncType))
        assert(isinstance(d, FuncType))

        self.assertEqual(a.params, [])
        self.assertIsNone(a.result)
        self.assertEqual(b.params, [('x', U32())])
        self.assertIsNone(a.result)
        self.assertEqual(c.params, [])
        self.assertEqual(c.result, String())
        self.assertEqual(d.params, [('a', U8()), ('b', U16())])
        self.assertEqual(d.result, U32())

        with self.assertRaises(WasmtimeError):
            FuncType()

    def test_primitives(self):
        self.assertEqual(simplety('bool'), Bool())
        self.assertEqual(simplety('u8'), U8())
        self.assertEqual(simplety('u16'), U16())
        self.assertEqual(simplety('u32'), U32())
        self.assertEqual(simplety('u64'), U64())
        self.assertEqual(simplety('s8'), S8())
        self.assertEqual(simplety('s16'), S16())
        self.assertEqual(simplety('s32'), S32())
        self.assertEqual(simplety('s64'), S64())
        self.assertEqual(simplety('f32'), F32())
        self.assertEqual(simplety('f64'), F64())
        self.assertEqual(simplety('char'), Char())
        self.assertEqual(simplety('string'), String())

    def test_list(self):
        l = simplety('(list u8)')
        assert(isinstance(l, ListType))
        self.assertEqual(l.element, U8())
        self.assertEqual(l, simplety('(list u8)'))
        self.assertNotEqual(l, simplety('(list u16)'))

    def test_record(self):
        r = namedty('(record (field "a" u8) (field "b" f32))')
        assert(isinstance(r, RecordType))
        self.assertEqual(r.fields, [('a', U8()), ('b', F32())])
        self.assertEqual(r, namedty('(record (field "a" u8) (field "b" f32))'))
        self.assertNotEqual(r, namedty('(record (field "a" u8) (field "b" f64))'))

    def test_tuple(self):
        t = namedty('(tuple u8 f32)')
        assert(isinstance(t, TupleType))
        self.assertEqual(t.elements, [U8(), F32()])
        self.assertEqual(t, namedty('(tuple u8 f32)'))
        self.assertNotEqual(t, namedty('(tuple u8 f64)'))

    def test_variant(self):
        t = namedty('(variant (case "a") (case "b" f32))')
        assert(isinstance(t, VariantType))
        self.assertEqual(t.cases, [('a', None), ('b', F32())])
        self.assertEqual(t, namedty('(variant (case "a") (case "b" f32))'))
        self.assertNotEqual(t, namedty('(variant (case "a") (case "b" f64))'))

    def test_enum(self):
        e = namedty('(enum "a" "b" "c")')
        assert(isinstance(e, EnumType))
        self.assertEqual(e.names, ['a', 'b', 'c'])
        self.assertEqual(e, namedty('(enum "a" "b" "c")'))
        self.assertNotEqual(e, namedty('(enum "a" "b" "d")'))

    def test_option(self):
        o = simplety('(option u32)')
        assert(isinstance(o, OptionType))
        self.assertEqual(o.payload, U32())
        self.assertEqual(o, simplety('(option u32)'))
        self.assertNotEqual(o, simplety('(option u64)'))

    def test_result(self):
        r = simplety('(result u32 (error f32))')
        assert(isinstance(r, ResultType))
        self.assertEqual(r.ok, U32())
        self.assertEqual(r.err, F32())
        self.assertEqual(r, simplety('(result u32 (error f32))'))

        r = simplety('(result (error f32))')
        assert(isinstance(r, ResultType))
        self.assertIsNone(r.ok)
        self.assertEqual(r.err, F32())

        r = simplety('(result u32)')
        assert(isinstance(r, ResultType))
        self.assertEqual(r.ok, U32())
        self.assertIsNone(r.err)

        r = simplety('(result)')
        assert(isinstance(r, ResultType))
        self.assertIsNone(r.ok)
        self.assertIsNone(r.err)

    def test_flags(self):
        f = namedty('(flags "a" "b" "c")')
        assert(isinstance(f, FlagsType))
        self.assertEqual(f.names, ['a', 'b', 'c'])
        self.assertEqual(f, namedty('(flags "a" "b" "c")'))
        self.assertNotEqual(f, namedty('(flags "a" "b" "d")'))

    def test_own_and_borrow(self):
        engine = Engine()
        c = Component(engine, f"""
        (component
            (import "r" (type $r (sub resource)))
            (import "a" (func (param "x" (borrow $r)) (result (own $r))))
        )
        """)
        fty = c.type.imports(engine)['a']
        assert(isinstance(fty, FuncType))
        _, param = fty.params[0]
        result = fty.result
        assert(isinstance(param, BorrowType))
        assert(isinstance(result, OwnType))
        self.assertEqual(param.ty, result.ty)
