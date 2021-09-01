from . import _ffi as ffi
from ctypes import *
from wasmtime import Engine, wat2wasm, ImportType, ExportType, WasmtimeError, ModuleType
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
        binary = (c_uint8 * len(wasm)).from_buffer_copy(wasm)
        ptr = POINTER(ffi.wasmtime_module_t)()
        error = ffi.wasmtime_module_new(engine._ptr, binary, len(wasm), byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._ptr = ptr

    @classmethod
    def _from_ptr(cls, ptr: "pointer[ffi.wasmtime_module_t]") -> "Module":
        ty: "Module" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasmtime_module_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
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

        ptr = POINTER(ffi.wasmtime_module_t)()

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        error = ffi.wasmtime_module_deserialize(
            engine._ptr,
            (c_uint8 * len(encoded)).from_buffer_copy(encoded),
            len(encoded),
            byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        ret: "Module" = cls.__new__(cls)
        ret._ptr = ptr
        return ret

    @classmethod
    def deserialize_file(cls, engine: Engine, path: str) -> 'Module':
        """
        Deserializes bytes previously created by `Module.serialize` that are
        stored in a file on the filesystem.

        Otherwise this function is the same as `Module.deserialize`.
        """

        ptr = POINTER(ffi.wasmtime_module_t)()
        path_bytes = path.encode('utf-8')
        error = ffi.wasmtime_module_deserialize_file(
            engine._ptr,
            path_bytes,
            byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        ret: "Module" = cls.__new__(cls)
        ret._ptr = ptr
        return ret

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
        buf = (c_uint8 * len(wasm)).from_buffer_copy(wasm)
        error = ffi.wasmtime_module_validate(engine._ptr, buf, len(wasm))

        if error:
            raise WasmtimeError._from_ptr(error)

    @property
    def type(self) -> ModuleType:
        """
        Gets the type of this module as a `ModuleType`
        """

        ptr = ffi.wasmtime_module_type(self._ptr)
        return ModuleType._from_ptr(ptr, None)

    @property
    def imports(self) -> typing.List[ImportType]:
        """
        Returns the types of imports that this module has
        """

        return self.type.imports

    @property
    def exports(self) -> typing.List[ExportType]:
        """
        Returns the types of the exports that this module has
        """
        return self.type.exports

    def serialize(self) -> bytearray:
        """
        Serializes this module to a binary representation.

        This method will serialize this module to an in-memory byte array which
        can be cached and later passed to `Module.deserialize` to recreate this
        module.
        """
        raw = ffi.wasm_byte_vec_t()
        err = ffi.wasmtime_module_serialize(self._ptr, byref(raw))
        if err:
            raise WasmtimeError._from_ptr(err)
        ret = ffi.to_bytes(raw)
        ffi.wasm_byte_vec_delete(byref(raw))
        return ret

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(module=self._ptr)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_MODULE, union)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasmtime_module_delete(self._ptr)
