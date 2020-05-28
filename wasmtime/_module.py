__all__ = [
    "Module",
]

from ctypes import byref, c_uint8

from ._error import WasmtimeError
from ._ffi import (dll, P_wasmtime_error_t, wasm_byte_vec_t, P_wasm_module_t,
                   wasm_importtype_vec_t, wasm_exporttype_vec_t)
from ._store import Store
from ._types import ImportType, ExportType
from ._wat2wasm import wat2wasm

dll.wasmtime_module_new.restype = P_wasmtime_error_t
dll.wasmtime_module_validate.restype = P_wasmtime_error_t


class Module:
    @classmethod
    def from_file(cls, store, path):
        """
        Compiles and creates a new `Module` by reading the file at `path` and
        then delegating to the `Module` constructor.
        """

        with open(path, "rb") as f:
            contents = f.read()
        return cls(store, contents)

    def __init__(self, store, wasm):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")

        # If this looks like a string, parse it as the text format. Note that
        # in python 2 strings and bytes are basically the same, so we skip this
        # if the first byte in the string is 0, meaning this is actually a wasm
        # module.
        if isinstance(wasm, str) and len(wasm) > 0 and ord(wasm[0]) != 0:
            wasm = wat2wasm(wasm)
        if isinstance(wasm, bytes) and len(wasm) > 0 and wasm[0] != 0:
            wasm = wat2wasm(wasm)

        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        c_ty = c_uint8 * len(wasm)
        binary = wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
        ptr = P_wasm_module_t()
        error = dll.wasmtime_module_new(store.__ptr__, byref(binary), byref(ptr))
        if error:
            raise WasmtimeError.__from_ptr__(error)
        self.__ptr__ = ptr
        self.store = store

    @classmethod
    def validate(cls, store, wasm):
        """
        Validates whether the list of bytes `wasm` provided is a valid
        WebAssembly binary given the configuration in `store`

        Raises a `WasmtimeError` if the wasm isn't valid.
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        c_ty = c_uint8 * len(wasm)
        binary = wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
        error = dll.wasmtime_module_validate(store.__ptr__, byref(binary))
        if error:
            raise WasmtimeError.__from_ptr__(error)

    @property
    def imports(self):
        """
        Returns the types of imports that this module has
        """

        imports = ImportTypeList()
        dll.wasm_module_imports(self.__ptr__, byref(imports.vec))
        ret = []
        for i in range(0, imports.vec.size):
            ret.append(ImportType.__from_ptr__(imports.vec.data[i], imports))
        return ret

    @property
    def exports(self):
        """
        Returns the types of the exports that this module has
        """

        exports = ExportTypeList()
        dll.wasm_module_exports(self.__ptr__, byref(exports.vec))
        ret = []
        for i in range(0, exports.vec.size):
            ret.append(ExportType.__from_ptr__(exports.vec.data[i], exports))
        return ret

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_module_delete(self.__ptr__)


class ImportTypeList:
    def __init__(self):
        self.vec = wasm_importtype_vec_t(0, None)

    def __del__(self):
        dll.wasm_importtype_vec_delete(byref(self.vec))


class ExportTypeList:
    def __init__(self):
        self.vec = wasm_exporttype_vec_t(0, None)

    def __del__(self):
        dll.wasm_exporttype_vec_delete(byref(self.vec))
