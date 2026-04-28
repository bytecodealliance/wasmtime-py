import ctypes
from . import _ffi as ffi
from ._managed import Managed
from wasmtime import WasmtimeError
from ._store import Storelike
from ._module import Module
from ._instance import Instance
from ._func import enter_wasm


class InstancePre(Managed["ctypes._Pointer[ffi.wasmtime_instance_pre_t]"]):
    """
    A pre-instantiated module with all imports already satisfied.

    `InstancePre` allows you to skip the import-resolution step on every call
    to `instantiate`, which can improve performance when creating many
    instances of the same module.

    Created via `Linker.instantiate_pre`.
    """

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_instance_pre_t]") -> None:
        ffi.wasmtime_instance_pre_delete(ptr)

    def instantiate(self, store: Storelike) -> Instance:
        """
        Instantiates the pre-linked module in the given store.

        Raises a `WasmtimeError` on error or a `wasmtime.Trap` if a trap occurs
        during instantiation.
        """
        instance = ffi.wasmtime_instance_t()
        with enter_wasm(store) as trap:
            error = ffi.wasmtime_instance_pre_instantiate(
                self.ptr(), store._context(), ctypes.byref(instance), trap)
            if error:
                raise WasmtimeError._from_ptr(error)
        return Instance._from_raw(instance)

    @property
    def module(self) -> Module:
        """
        Returns the `Module` that this `InstancePre` was
        created from.
        """
        ptr = ffi.wasmtime_instance_pre_module(self.ptr())
        return Module._from_ptr(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_instance_pre_t]") -> 'InstancePre':
        if not isinstance(ptr, ctypes.POINTER(ffi.wasmtime_instance_pre_t)):
            raise TypeError("wrong pointer type")
        pre: InstancePre = cls.__new__(cls)
        pre._set_ptr(ptr)
        return pre
