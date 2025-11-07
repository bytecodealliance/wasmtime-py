from . import _ffi as ffi
from ._wat2wasm import _to_wasm
import ctypes
from wasmtime import Engine, wat2wasm, ImportType, ExportType, WasmtimeError, Managed
import typing
from os import PathLike


class Module(Managed["ctypes._Pointer[ffi.wasmtime_module_t]"]):

    @classmethod
    def from_file(cls, engine: Engine, path: typing.Union[str, bytes, PathLike]) -> "Module":
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

        wasm = _to_wasm(wasm)

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        binary = (ctypes.c_uint8 * len(wasm)).from_buffer_copy(wasm)
        ptr = ctypes.POINTER(ffi.wasmtime_module_t)()
        error = ffi.wasmtime_module_new(engine.ptr(), binary, len(wasm), ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._set_ptr(ptr)

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_module_t]") -> None:
        ffi.wasmtime_module_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_module_t]") -> "Module":
        if not isinstance(ptr, ctypes.POINTER(ffi.wasmtime_module_t)):
            raise TypeError("wrong pointer type")
        ty: "Module" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @classmethod
    def deserialize(cls, engine: Engine, encoded: typing.Union[bytes, bytearray]) -> 'Module':
        """
        Deserializes bytes previously created by `Module.serialize`.

        This constructor for `Module` will deserialize bytes previously created
        by a serialized module. This will only succeed if the bytes were
        previously created by the same version of `wasmtime` as well as the
        same configuration within `Engine`.
        """

        if not isinstance(encoded, (bytes, bytearray)):
            raise TypeError("expected bytes")

        ptr = ctypes.POINTER(ffi.wasmtime_module_t)()

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        error = ffi.wasmtime_module_deserialize(
            engine.ptr(),
            (ctypes.c_uint8 * len(encoded)).from_buffer_copy(encoded),
            len(encoded),
            ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return cls._from_ptr(ptr)

    @classmethod
    def deserialize_file(cls, engine: Engine, path: str) -> 'Module':
        """
        Deserializes bytes previously created by `Module.serialize` that are
        stored in a file on the filesystem.

        Otherwise this function is the same as `Module.deserialize`.
        """

        ptr = ctypes.POINTER(ffi.wasmtime_module_t)()
        path_bytes = path.encode('utf-8')
        error = ffi.wasmtime_module_deserialize_file(
            engine.ptr(),
            path_bytes,
            ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return cls._from_ptr(ptr)

    @classmethod
    def validate(cls, engine: Engine, wasm: typing.Union[bytes, bytearray]) -> None:
        """
        Validates whether the list of bytes `wasm` provided is a valid
        WebAssembly binary given the configuration in `store`

        Raises a `WasmtimeError` if the wasm isn't valid.
        """

        if not isinstance(wasm, (bytes, bytearray)):
            raise TypeError("expected wasm bytes")

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        buf = (ctypes.c_uint8 * len(wasm)).from_buffer_copy(wasm)
        error = ffi.wasmtime_module_validate(engine.ptr(), buf, len(wasm))

        if error:
            raise WasmtimeError._from_ptr(error)

    @property
    def imports(self) -> typing.List[ImportType]:
        """
        Returns the types of imports that this module has
        """

        imports = ImportTypeList()
        ffi.wasmtime_module_imports(self.ptr(), ctypes.byref(imports.vec))
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
        ffi.wasmtime_module_exports(self.ptr(), ctypes.byref(exports.vec))
        ret = []
        for i in range(0, exports.vec.size):
            ret.append(ExportType._from_ptr(exports.vec.data[i], exports))
        return ret

    def serialize(self) -> bytearray:
        """
        Serializes this module to a binary representation.

        This method will serialize this module to an in-memory byte array which
        can be cached and later passed to `Module.deserialize` to recreate this
        module.
        """
        raw = ffi.wasm_byte_vec_t()
        err = ffi.wasmtime_module_serialize(self.ptr(), ctypes.byref(raw))
        if err:
            raise WasmtimeError._from_ptr(err)
        ret = ffi.to_bytes(raw)
        ffi.wasm_byte_vec_delete(ctypes.byref(raw))
        return ret


class ImportTypeList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_importtype_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_importtype_vec_delete(ctypes.byref(self.vec))


class ExportTypeList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_exporttype_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_exporttype_vec_delete(ctypes.byref(self.vec))
