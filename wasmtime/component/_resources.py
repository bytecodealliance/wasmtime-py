from .. import _ffi as ffi, WasmtimeError, Managed, Storelike, WasmtimeError
from ctypes import POINTER, byref
import ctypes
from ._resource_type import ResourceType
from ._enter import enter_wasm


class ResourceAny(Managed["ctypes._Pointer[ffi.wasmtime_component_resource_any_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ResourceAny`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_any_t]") -> None:
        ffi.wasmtime_component_resource_any_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_any_t]") -> "ResourceAny":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_resource_any_t)):
            raise TypeError("wrong pointer type")
        ty: "ResourceAny" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def type(self) -> ResourceType:
        """
        Returns the `ResourceType` of this `ResourceAny`.
        """
        ptr = ffi.wasmtime_component_resource_any_type(self.ptr())
        return ResourceType._from_ptr(ptr)

    @property
    def owned(self) -> bool:
        """
        Returns whether this `ResourceAny` is an `own` resource or a `borrow`
        resource.
        """
        return ffi.wasmtime_component_resource_any_owned(self.ptr())

    def drop(self, store: Storelike) -> None:
        """
        Runs the WebAssembly-defined destructor, if any, for this resource.

        This is required to be called to clean up state information in the
        store about this resource. This may execute WebAssembly code if the
        resource is a guest-owned resource with a defined destructor.
        """
        def run() -> 'ctypes._Pointer[ffi.wasmtime_error_t]':
            return ffi.wasmtime_component_resource_any_drop(store._context(), self.ptr())
        enter_wasm(run)

    def to_host(self, store: Storelike) -> "ResourceHost":
        """
        Attempts to downcast this `ResourceAny` to a `ResourceHost`.

        This will raise a `WasmtimeError` if this `ResourceAny` is not
        actually a host-defined resource.
        """
        ptr = POINTER(ffi.wasmtime_component_resource_host_t)()
        error = ffi.wasmtime_component_resource_any_to_host(store._context(), self.ptr(), byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return ResourceHost._from_ptr(ptr)


class ResourceHost(Managed["ctypes._Pointer[ffi.wasmtime_component_resource_host_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ResourceHost`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_host_t]") -> None:
        ffi.wasmtime_component_resource_host_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_resource_host_t]") -> "ResourceHost":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_resource_host_t)):
            raise TypeError("wrong pointer type")
        ty: "ResourceHost" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @classmethod
    def own(cls, rep: int, ty: int) -> "ResourceHost":
        ptr = ffi.wasmtime_component_resource_host_new(True, rep, ty)
        return cls._from_ptr(ptr)

    @classmethod
    def borrow(cls, rep: int, ty: int) -> "ResourceHost":
        ptr = ffi.wasmtime_component_resource_host_new(False, rep, ty)
        return cls._from_ptr(ptr)

    @property
    def rep(self) -> int:
        """
        Returns the integer representation associated with this host resource.
        """
        return ffi.wasmtime_component_resource_host_rep(self.ptr())

    @property
    def type(self) -> int:
        """
        Returns the integer type identifier associated with this host resource.
        """
        return ffi.wasmtime_component_resource_host_type(self.ptr())

    @property
    def owned(self) -> bool:
        """
        Returns whether this `ResourceHost` is an `own` resource or a `borrow`
        resource.
        """
        return ffi.wasmtime_component_resource_host_owned(self.ptr())

    def to_any(self, store: Storelike) -> ResourceAny:
        """
        Upcasts this `ResourceHost` to a `ResourceAny`.
        """
        ptr = POINTER(ffi.wasmtime_component_resource_any_t)()
        error = ffi.wasmtime_component_resource_host_to_any(store._context(), self.ptr(), byref(ptr))
        if error:
            raise WasmtimeError._from_ptr(error)
        return ResourceAny._from_ptr(ptr)
