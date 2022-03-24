from . import _ffi as ffi
from ctypes import POINTER, byref
from wasmtime import Module, WasmtimeError
from ._extern import wrap_extern, get_extern_ptr
from ._exportable import AsExtern
from typing import Sequence, Union, Optional, Mapping, Iterable
from ._store import Storelike
from ._func import enter_wasm


class Instance:
    _instance: ffi.wasmtime_instance_t
    _exports: Optional["InstanceExports"]

    def __init__(self, store: Storelike, module: Module, imports: Sequence[AsExtern]):
        """
        Creates a new instance by instantiating the `module` given with the
        `imports` into the `store` provided.

        The `store` must have type `Store`, the `module` must have type
        `Module`, and the `imports` must be an iterable of external values,
        either `Extern`, `Func`, `Table`, `Memory`, or `Global`.

        Raises an error if instantiation fails (e.g. linking or trap) and
        otherwise initializes the new instance.
        """

        imports_ptr = (ffi.wasmtime_extern_t * len(imports))()
        for i, val in enumerate(imports):
            imports_ptr[i] = get_extern_ptr(val)

        instance = ffi.wasmtime_instance_t()
        trap = POINTER(ffi.wasm_trap_t)()
        with enter_wasm(store) as trap:
            error = ffi.wasmtime_instance_new(
                store._context,
                module._ptr,
                imports_ptr,
                len(imports),
                byref(instance),
                trap)
            if error:
                raise WasmtimeError._from_ptr(error)
        self._instance = instance
        self._exports = None

    @classmethod
    def _from_raw(cls, instance: ffi.wasmtime_instance_t) -> "Instance":
        ty: "Instance" = cls.__new__(cls)
        ty._exports = None
        ty._instance = instance
        return ty

    def exports(self, store: Storelike) -> "InstanceExports":
        """
        Returns the exports of this module

        The returned type can be indexed both with integers and with strings for
        names of exports.
        """
        if self._exports is None:
            self._exports = InstanceExports(store, self)
        return self._exports

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(instance=self._instance)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_INSTANCE, union)


class InstanceExports:
    _extern_list: Sequence[AsExtern]
    _extern_map: Mapping[str, AsExtern]

    def __init__(self, store: Storelike, instance: Instance):
        self._extern_list = []
        self._extern_map = {}

        i = 0
        item = ffi.wasmtime_extern_t()
        name_ptr = POINTER(ffi.c_char)()
        name_len = ffi.c_size_t(0)
        while ffi.wasmtime_instance_export_nth(
                store._context,
                byref(instance._instance),
                i,
                byref(name_ptr),
                byref(name_len),
                byref(item)):
            name = ffi.to_str_raw(name_ptr, name_len.value)
            extern = wrap_extern(item)
            self._extern_list.append(extern)
            self._extern_map[name] = extern
            i += 1
            item = ffi.wasmtime_extern_t()

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
