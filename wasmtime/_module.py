from ._ffi import *
from ctypes import *
from wasmtime import Store, wat2wasm, ImportType, ExportType

dll.wasm_module_new.restype = P_wasm_module_t
dll.wasm_module_validate.restype = c_bool


class Module(object):
    def __init__(self, store, wasm):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")

        # If this looks like a string, parse it as the text format. Note that
        # in python 2 strings and bytes are basically the same, so we skip this
        # if the first byte in the string is 0, meaning this is actually a wasm
        # module.
        if isinstance(wasm, str) and len(wasm) > 0 and ord(wasm[0]) != 0:
            wasm = wat2wasm(wasm)

        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        c_ty = c_uint8 * len(wasm)
        binary = wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
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

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        c_ty = c_uint8 * len(wasm)
        binary = wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
        ok = dll.wasm_module_validate(store.__ptr__, byref(binary))
        if ok:
            return True
        else:
            return False

    # Returns the types of imports that this module has
    def imports(self):
        imports = ImportTypeList()
        dll.wasm_module_imports(self.__ptr__, byref(imports.vec))
        ret = []
        for i in range(0, imports.vec.size):
            ret.append(ImportType.__from_ptr__(imports.vec.data[i], imports))
        return ret

    # Returns the types of the exports that this module has
    def exports(self):
        exports = ExportTypeList()
        dll.wasm_module_exports(self.__ptr__, byref(exports.vec))
        ret = []
        for i in range(0, exports.vec.size):
            ret.append(ExportType.__from_ptr__(exports.vec.data[i], exports))
        return ret

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_module_delete(self.__ptr__)


class ImportTypeList(object):
    def __init__(self):
        self.vec = wasm_importtype_vec_t(0, None)

    def __del__(self):
        dll.wasm_importtype_vec_delete(byref(self.vec))


class ExportTypeList(object):
    def __init__(self):
        self.vec = wasm_exporttype_vec_t(0, None)

    def __del__(self):
        dll.wasm_exporttype_vec_delete(byref(self.vec))
