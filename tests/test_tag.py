import unittest
from wasmtime import *


class TestTag(unittest.TestCase):
    def test_new(self):
        store = Store()
        functype = FuncType([ValType.i32()], [])
        tagtype = TagType(functype)
        tag = Tag(store, tagtype)
        self.assertIsNotNone(tag)

    def test_type(self):
        functype = FuncType([ValType.i32()], [])
        tagtype = TagType(functype)

        self.assertEqual(tagtype.functype.params, [ValType.i32()])
        self.assertEqual(tagtype.functype.results, [])

        config = Config()
        config.wasm_exceptions = True
        engine = Engine(config)

        module = Module(engine, """
            (module
                (tag (export "mytag") (param i32))
            )
        """)
        ty = module.exports[0].type
        assert isinstance(ty, TagType)
        self.assertEqual(ty.functype.params, [ValType.i32()])
        self.assertEqual(ty.functype.results, [])

        store = Store(engine)
        tag = Tag(store, tagtype)
        retrieved = tag.type(store)
        self.assertIsInstance(retrieved, TagType)

    def test_eq(self):
        store = Store()
        functype = FuncType([ValType.i32()], [])
        tagtype = TagType(functype)
        tag1 = Tag(store, tagtype)
        tag2 = Tag(store, tagtype)
        self.assertFalse(tag1.eq(store, tag2))
        self.assertTrue(tag1.eq(store, tag1))

    def test_wrong_type(self):
        store = Store()
        with self.assertRaises(TypeError):
            Tag(store, "not a tagtype")  # type: ignore

    def test_tag_import(self):
        config = Config()
        config.wasm_exceptions = True
        engine = Engine(config)

        module = Module(engine, """
            (module (import "" "" (tag)))
        """)
        store = Store(engine)
        with self.assertRaises(WasmtimeError):
            Instance(store, module, [])
        Instance(store, module, [Tag(store, TagType(FuncType([], [])))])

    def test_tag_export(self):
        config = Config()
        config.wasm_exceptions = True
        engine = Engine(config)

        module = Module(engine, """
            (module (tag (export "")))
        """)
        store = Store(engine)
        i = Instance(store, module, [])
        tag = i.exports(store)['']
        assert isinstance(tag, Tag)
        self.assertEqual(tag.type(store).functype.params, [])
        self.assertEqual(tag.type(store).functype.results, [])
