from ._ffi import *
from ctypes import *
from wasmtime import Engine

dll.wasm_store_new.restype = P_wasm_store_t


class Store(object):
    def __init__(self, engine=None):
        if engine is None:
            engine = Engine()
        elif not isinstance(engine, Engine):
            raise TypeError("expected an Engine")
        self.__ptr__ = dll.wasm_store_new(engine.__ptr__)
        self.engine = engine

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_store_delete(self.__ptr__)
