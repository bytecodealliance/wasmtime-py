import unittest

from wasmtime import *


def ref_types_store():
    config = Config()
    config.wasm_reference_types = True
    engine = Engine(config)
    return Store(engine)


def compile_and_instantiate(wat):
    store = ref_types_store()
    module = Module(store.engine, wat)
    return (Instance(store, module, []), store)


class SetHitOnDrop:
    def __init__(self, obj):
        obj['hit'] = False
        self.obj = obj

    def __del__(self):
        self.obj['hit'] = True


class TestExternRef(unittest.TestCase):
    def test_smoke(self):
        (instance, store) = compile_and_instantiate(
            """
            (module
                 (func (export "f") (param externref) (result externref)
                     local.get 0
                 )
                 (func (export "null_externref") (result externref)
                     ref.null extern
                 )
            )
            """
        )

        null_externref = instance.exports(store).get("null_externref")
        self.assertEqual(null_externref(store), None)

        f = instance.exports(store).get("f")
        externs = [42, True, False, None, "Hello", {"x": 1}, [12, 13, 14], Config()]

        for extern in externs:
            # We can create an externref for the given extern data.
            ref = Val.externref(extern)

            # And the externref's value is our extern data.
            self.assertEqual(ref.value, extern)

            # And we can round trip the externref through Wasm and still get our
            # extern data.
            result = f(store, ref)
            self.assertEqual(result, extern)

    def test_externref_tables(self):
        store = ref_types_store()
        ty = TableType(ValType.externref(), Limits(10, None))
        table = Table(store, ty, "init")

        for i in range(0, 10):
            self.assertEqual(table.get(store, i), "init")

        table.grow(store, 2, "grown")

        for i in range(0, 10):
            self.assertEqual(table.get(store, i), "init")
        for i in range(10, 12):
            self.assertEqual(table.get(store, i), "grown")

        table.set(store, 7, "lucky")

        for i in range(0, 7):
            self.assertEqual(table.get(store, i), "init")
        self.assertEqual(table.get(store, 7), "lucky")
        for i in range(8, 10):
            self.assertEqual(table.get(store, i), "init")
        for i in range(10, 12):
            self.assertEqual(table.get(store, i), "grown")

    def test_externref_in_global(self):
        store = ref_types_store()
        ty = GlobalType(ValType.externref(), True)
        g = Global(store, ty, Val.externref("hello"))
        self.assertEqual(g.value(store), "hello")
        g.set_value(store, "goodbye")
        self.assertEqual(g.value(store), "goodbye")

    def test_dtor_global(self):
        obj = {}  # type: ignore
        store = ref_types_store()
        ty = GlobalType(ValType.externref(), True)
        g = Global(store, ty, Val.externref(SetHitOnDrop(obj)))
        assert(not obj['hit'])
        g.set_value(store, None)
        assert(obj['hit'])

    def test_dtor_func(self):
        (instance, store) = compile_and_instantiate(
            """
            (module
                 (func (export "f") (param externref))
            )
            """
        )

        f = instance.exports(store).get("f")
        obj = {}  # type: ignore
        f(store, SetHitOnDrop(obj))
        store.gc()
        assert(obj['hit'])


class TestFuncRef(unittest.TestCase):
    def test_smoke(self):
        (instance, store) = compile_and_instantiate(
            """
            (module
                 (func (export \"f\") (param funcref) (result funcref)
                     local.get 0
                 )
                 (func (export "null_funcref") (result funcref)
                     ref.null func
                 )
            )
            """
        )

        null_funcref = instance.exports(store).get("null_funcref")
        self.assertEqual(null_funcref(store), None)

        f = instance.exports(store).get("f")

        ty = FuncType([], [ValType.i32()])
        g = Func(store, ty, lambda: 42)

        # We can create a funcref.
        ref_g_val = Val.funcref(g)

        # And the funcref's points to `g`.
        g2 = ref_g_val.as_funcref()
        if isinstance(g2, Func):
            self.assertEqual(g2(store), 42)
        else:
            self.fail("g2 is not a funcref: g2 = %r" % g2)

        # And we can round trip the funcref through Wasm.
        g3 = f(store, ref_g_val)
        if isinstance(g3, Func):
            self.assertEqual(g3(store), 42)
        else:
            self.fail("g3 is not a funcref: g3 = %r" % g3)
