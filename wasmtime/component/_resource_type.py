from .. import _ffi as ffi, WasmtimeError
from ctypes import POINTER
import ctypes
from wasmtime import Managed


class ResourceType(Managed["ctypes._Pointer[ffi.wasmtime_component_resource_type_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ResourceType`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_type_t]") -> None:
        ffi.wasmtime_component_resource_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_type_t]") -> "ResourceType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_resource_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ResourceType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @classmethod
    def host(cls, val: int) -> "ResourceType":
        """
        Creates a new `ResourceType` representing a host-defined resource
        identified by the integer identifier `val` given.
        """
        ptr = ffi.wasmtime_component_resource_type_new_host(val)
        return cls._from_ptr(ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResourceType):
            return False
        return ffi.wasmtime_component_resource_type_equal(self.ptr(), other.ptr())
