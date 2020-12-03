import unittest

from wasmtime import *


class TestModuleLinking(unittest.TestCase):
    def store(self):
        config = Config()
        config.wasm_module_linking = True
        return Store(Engine(config))

    def test_import_string_optional(self):
        store = self.store()
        module = Module(store.engine, """
            (module
                (import "" (func))
            )
        """)
        assert(module.type.imports[0].module == '')
        assert(module.type.imports[0].name is None)

    def test_module_import(self):
        store = self.store()
        module1 = Module(store.engine, """
            (module (import "" (module)))
        """)
        module2 = Module(store.engine, "(module)")
        Instance(store, module1, [module2])

    def test_module_export(self):
        store = self.store()
        module = Module(store.engine, """
            (module (module (export "")))
        """)
        i = Instance(store, module, [])
        assert(isinstance(i.exports[0], Module))

    def test_instance_import(self):
        store = self.store()
        module = Module(store.engine, """
            (module (import "" (instance)))
        """)
        instance = Instance(store, Module(store.engine, "(module)"), [])
        Instance(store, module, [instance])

    def test_instance_export(self):
        store = self.store()
        instance = Module(store.engine, """
            (module
                (module $m)
                (instance (export "") (instantiate $m))
            )
        """)
        i = Instance(store, instance, [])
        assert(isinstance(i.exports[0], Instance))
