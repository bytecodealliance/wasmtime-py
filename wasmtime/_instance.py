from . import _ffi as ffi
from ctypes import POINTER, pointer, byref
from wasmtime import Module, Trap, WasmtimeError, Store, InstanceType
from ._extern import wrap_extern, get_extern_ptr
from ._exportable import AsExtern
from typing import Sequence, Union, Optional, Mapping, Iterable, Any


class Instance:
    _ptr: "pointer[ffi.wasm_instance_t]"
    _module: Module
    _exports: Optional["InstanceExports"]
    _owner: Optional[Any]

    def __init__(self, store: Store, module: Module, imports: Sequence[AsExtern]):
        """
        Creates a new instance by instantiating the `module` given with the
        `imports` into the `store` provided.

        The `store` must have type `Store`, the `module` must have type
        `Module`, and the `imports` must be an iterable of external values,
        either `Extern`, `Func`, `Table`, `Memory`, or `Global`.

        Raises an error if instantiation fails (e.g. linking or trap) and
        otherwise initializes the new instance.
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(module, Module):
            raise TypeError("expected a Module")

        imports_ptr = (POINTER(ffi.wasm_extern_t) * len(imports))()
        for i, val in enumerate(imports):
            imports_ptr[i] = get_extern_ptr(val)
        imports_arg = ffi.wasm_extern_vec_t(len(imports), imports_ptr)

        instance = POINTER(ffi.wasm_instance_t)()
        trap = POINTER(ffi.wasm_trap_t)()
        error = ffi.wasmtime_instance_new(
            store._ptr,
            module._ptr,
            byref(imports_arg),
            byref(instance),
            byref(trap))
        if error:
            raise WasmtimeError._from_ptr(error)
        if trap:
            raise Trap._from_ptr(trap)
        self._ptr = instance
        self._exports = None
        self._owner = None

    @classmethod
    def _from_ptr(cls, ptr: 'pointer[ffi.wasm_instance_t]', owner: Optional[Any]) -> "Instance":
        ty: "Instance" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_instance_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty._exports = None
        ty._owner = owner
        return ty

    @property
    def type(self) -> InstanceType:
        """
        Gets the type of this instance as an `InstanceType`
        """

        ptr = ffi.wasm_instance_type(self._ptr)
        return InstanceType._from_ptr(ptr, None)

    @property
    def exports(self) -> "InstanceExports":
        """
        Returns the exports of this module

        The returned type can be indexed both with integers and with strings for
        names of exports.
        """
        if self._exports is None:
            externs = ExternTypeList()
            ffi.wasm_instance_exports(self._ptr, byref(externs.vec))
            extern_list = []
            for i in range(0, externs.vec.size):
                extern_list.append(wrap_extern(externs.vec.data[i], externs))
            self._exports = InstanceExports(extern_list, self.type)
        return self._exports

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_instance_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_owner') and self._owner is None:
            ffi.wasm_instance_delete(self._ptr)


class InstanceExports:
    _extern_list: Sequence[AsExtern]
    _extern_map: Mapping[str, AsExtern]

    def __init__(self, extern_list: Sequence[AsExtern], ty: InstanceType):
        self._extern_list = extern_list
        self._extern_map = {}
        exports = ty.exports
        for i, extern in enumerate(extern_list):
            self._extern_map[exports[i].name] = extern

    def __getitem__(self, idx: Union[int, str]) -> AsExtern:
        ret = self.get(idx)
        if ret is None:
            msg = "failed to find export {}".format(idx)
            if isinstance(idx, str):
                raise KeyError(msg)
            raise IndexError(msg)
        return ret

    def __len__(self) -> int:
        return len(self._extern_list)

    def __iter__(self) -> Iterable[AsExtern]:
        return iter(self._extern_list)

    def get(self, idx: Union[int, str]) -> Optional[AsExtern]:
        if isinstance(idx, str):
            return self._extern_map.get(idx)
        if idx < len(self._extern_list):
            return self._extern_list[idx]
        return None


class ExternTypeList:
    def __init__(self) -> None:
        self.vec = ffi.wasm_extern_vec_t(0, None)

    def __del__(self) -> None:
        ffi.wasm_extern_vec_delete(byref(self.vec))
