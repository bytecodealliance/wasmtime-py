from .ffi import *
from ctypes import *
from wasmtime import Store, wat2wasm, ImportType, ExportType

dll.wasm_module_new.restype = P_wasm_module_t

class Module:
    def __init__(self, store, wasm):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        # If this looks like a string, parse it as the text format
        if isinstance(wasm, str):
            wasm = wat2wasm(store.engine, wasm)
        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        binary = wasm_byte_vec_t(len(wasm), cast(wasm, POINTER(c_uint8)))
        ptr = dll.wasm_module_new(store.__ptr__, byref(binary))
        if not ptr:
            raise RuntimeError("failed to compile module")
        self.__ptr__ = ptr
        self.store = store

    @classmethod
    def validate(cls, store, wasm):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        binary = wasm_byte_vec_t(len(wasm), cast(wasm, POINTER(c_uint8)))
        ok = dll.wasm_module_validate(store.__ptr__, byref(binary))
        if ok:
            return True
        else:
            return False

    # Returns the types of imports that this module has
    def imports(self):
        imports = wasm_importtype_vec_t()
        dll.wasm_module_imports(self.__ptr__, byref(imports))
        ret = []
        for i in range(0, imports.size):
            ret.append(ImportType.__from_ptr__(imports.data[i], None))
        return ret

    # Returns the types of the exports that this module has
    def exports(self):
        exports = wasm_exporttype_vec_t()
        dll.wasm_module_exports(self.__ptr__, byref(exports))
        ret = []
        for i in range(0, exports.size):
            ret.append(ExportType.__from_ptr__(exports.data[i], None))
        return ret

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_module_delete(self.__ptr__)
