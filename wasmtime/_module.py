from . import _ffi as ffi
from ctypes import *
from wasmtime import Store, Engine, wat2wasm, ImportType, ExportType, WasmtimeError
import typing


class Module:
    @classmethod
    def from_file(cls, engine: Engine, path: str) -> "Module":
        """
        Compiles and creates a new `Module` by reading the file at `path` and
        then delegating to the `Module` constructor.
        """

        with open(path, "rb") as f:
            contents = f.read()
        return cls(engine, contents)

    def __init__(self, engine: Engine, wasm: typing.Union[str, bytes]):
        if not isinstance(engine, Engine):
            raise TypeError("expected an Engine")

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
        binary = ffi.wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
        ptr = POINTER(ffi.wasm_module_t)()
        error = ffi.wasmtime_module_new(engine._ptr, byref(binary), byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._ptr = ptr
        self.engine = engine

    @classmethod
    def validate(cls, store: Store, wasm: typing.Union[bytes, bytearray]) -> None:
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
        binary = ffi.wasm_byte_vec_t(len(wasm), c_ty.from_buffer_copy(wasm))
        error = ffi.wasmtime_module_validate(store._ptr, byref(binary))
        if error:
            raise WasmtimeError._from_ptr(error)

    @property
    def imports(self) -> typing.List[ImportType]:
        """
        Returns the types of imports that this module has
        """

        imports = ImportTypeList()
        ffi.wasm_module_imports(self._ptr, byref(imports.vec))
        ret = []
        for i in range(0, imports.vec.size):
            ret.append(ImportType._from_ptr(imports.vec.data[i], imports))
        return ret

    @property
    def exports(self) -> typing.List[ExportType]:
        """
        Returns the types of the exports that this module has
        """

        exports = ExportTypeList()
        ffi.wasm_module_exports(self._ptr, byref(exports.vec))
        ret = []
        for i in range(0, exports.vec.size):
            ret.append(ExportType._from_ptr(exports.vec.data[i], exports))
        return ret

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasm_module_delete(self._ptr)


class ImportTypeList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_importtype_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_importtype_vec_delete(byref(self.vec))


class ExportTypeList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_exporttype_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_exporttype_vec_delete(byref(self.vec))
