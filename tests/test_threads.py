import unittest

from wasmtime import *


class TestThreads(unittest.TestCase):
    def test_threads(self):
        config = Config()
        config.wasm_threads = True

        engine = Engine(config)
        linker = Linker(engine)
        store = Store(engine)

        linker.define_wasi()

        wasi_config = WasiConfig()
        wasi_config.argv = ['3']
        wasi_config.inherit_argv()
        wasi_config.inherit_stdout()
        store.set_wasi(wasi_config)

        module = Module.from_file(engine, 'tests/threads.wasm')
        # linker.define_wasi_threads(store, module)
        # instance = linker.instantiate(store, module)
        # instance.exports(store)["_start"](store)


