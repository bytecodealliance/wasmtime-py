from .. import _ffi as ffi
from .._wat2wasm import _to_wasm
from ._types import ComponentType
import ctypes
from wasmtime import Engine, wat2wasm, WasmtimeError, Managed, Module
import typing
from os import PathLike


class ExportIndex(Managed["ctypes._Pointer[ffi.wasmtime_component_export_index_t]"]):

    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct an `ExportIndex`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_export_index_t]") -> None:
        ffi.wasmtime_component_export_index_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_export_index_t]") -> "ExportIndex":
        if not isinstance(ptr, ctypes.POINTER(ffi.wasmtime_component_export_index_t)):
            raise TypeError("wrong pointer type")
        ty: "ExportIndex" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty


class Component(Managed["ctypes._Pointer[ffi.wasmtime_component_t]"]):

    @classmethod
    def from_file(cls, engine: Engine, path: typing.Union[str, bytes, PathLike]) -> "Component":
        """
        Compiles and creates a new `Component` by reading the file at `path` and
        then delegating to the `Component` constructor.
        """

        with open(path, "rb") as f:
            contents = f.read()
        return cls(engine, contents)

    def __init__(self, engine: Engine, wasm: typing.Union[str, bytes, bytearray]):
        if not isinstance(engine, Engine):
            raise TypeError("expected an Engine")

        wasm = _to_wasm(wasm)

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        binary = (ctypes.c_uint8 * len(wasm)).from_buffer_copy(wasm)
        ptr = ctypes.POINTER(ffi.wasmtime_component_t)()
        error = ffi.wasmtime_component_new(engine.ptr(), binary, len(wasm), ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._set_ptr(ptr)

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_t]") -> None:
        ffi.wasmtime_component_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_t]") -> "Component":
        if not isinstance(ptr, ctypes.POINTER(ffi.wasmtime_component_t)):
            raise TypeError("wrong pointer type")
        ty: "Component" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @classmethod
    def deserialize(cls, engine: Engine, encoded: typing.Union[bytes, bytearray]) -> 'Component':
        """
        Deserializes bytes previously created by `Component.serialize`.

        This constructor for `Component` will deserialize bytes previously created
        by a serialized component. This will only succeed if the bytes were
        previously created by the same version of `wasmtime` as well as the
        same configuration within `Engine`.
        """

        if not isinstance(encoded, (bytes, bytearray)):
            raise TypeError("expected bytes")

        ptr = ctypes.POINTER(ffi.wasmtime_component_t)()

        # TODO: can the copy be avoided here? I can't for the life of me
        # figure this out.
        error = ffi.wasmtime_component_deserialize(
            engine.ptr(),
            (ctypes.c_uint8 * len(encoded)).from_buffer_copy(encoded),
            len(encoded),
            ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return cls._from_ptr(ptr)

    @classmethod
    def deserialize_file(cls, engine: Engine, path: str) -> 'Component':
        """
        Deserializes bytes previously created by `Component.serialize` that are
        stored in a file on the filesystem.

        Otherwise this function is the same as `Component.deserialize`.
        """

        ptr = ctypes.POINTER(ffi.wasmtime_component_t)()
        path_bytes = path.encode('utf-8')
        error = ffi.wasmtime_component_deserialize_file(
            engine.ptr(),
            path_bytes,
            ctypes.byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return cls._from_ptr(ptr)

    def serialize(self) -> bytearray:
        """
        Serializes this component to a binary representation.

        This method will serialize this component to an in-memory byte array
        which can be cached and later passed to `Component.deserialize` to
        recreate this component.
        """
        raw = ffi.wasm_byte_vec_t()
        err = ffi.wasmtime_component_serialize(self.ptr(), ctypes.byref(raw))
        if err:
            raise WasmtimeError._from_ptr(err)
        ret = ffi.to_bytes(raw)
        ffi.wasm_byte_vec_delete(ctypes.byref(raw))
        return ret

    def get_export_index(self, name: str, instance : typing.Optional[ExportIndex] = None) -> typing.Optional[ExportIndex]:
        """
        Gets an `ExportIndex` from this component pointing to a specific item
        in this component.

        The returned `ExportIndex` can later be used to lookup exports on an
        instance or it can be used to lookup further indexes if it points to an
        instance for example.
        """
        name_bytes = name.encode('utf-8')
        name_buf = ctypes.create_string_buffer(name_bytes)
        ret = ffi.wasmtime_component_get_export_index(
            self.ptr(),
            instance.ptr() if instance is not None else None,
            name_buf,
            len(name_bytes))
        if not ret:
            return None
        return ExportIndex._from_ptr(ret)

    @property
    def type(self) -> ComponentType:
        """
        Returns the `ComponentType` corresponding to this component.
        """
        ptr = ffi.wasmtime_component_type(self.ptr())
        return ComponentType._from_ptr(ptr)
