from .. import _ffi as ffi, WasmtimeError, Storelike
from ctypes import byref
from typing import Optional, Union
from ._component import ExportIndex
from ._func import Func


class Instance:
    _instance: ffi.wasmtime_component_instance_t

    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct an `Instance`")

    @classmethod
    def _from_raw(cls, instance: ffi.wasmtime_component_instance_t) -> "Instance":
        ty: "Instance" = cls.__new__(cls)
        ty._instance = instance
        return ty

    def get_export_index(self, store: Storelike, name: str, instance: Optional[ExportIndex] = None) -> Optional[ExportIndex]:
        """
        Retrieves the export index for the export named `name` from this
        component instance.

        If `instance` is provided then the export is looked up within that
        nested instance.

        Returns `None` if no such export exists otherwise returns the export
        index.
        """
        name_bytes = name.encode('utf-8')
        name_buf = ffi.create_string_buffer(name_bytes)

        ptr = ffi.wasmtime_component_instance_get_export_index(
            byref(self._instance),
            store._context(),
            instance.ptr() if instance is not None else None,
            name_buf,
            len(name_bytes))
        if ptr:
            return ExportIndex._from_ptr(ptr)
        return None

    def get_func(self, store: Storelike, index: Union[ExportIndex, str]) -> Optional[Func]:
        """
        Retrieves the function export for the given export index.

        Returns `None` if the export index does not correspond to a function
        export and otherwise returns the function.
        """
        if isinstance(index, str):
            ei = self.get_export_index(store, index)
            if ei is None:
                return None
            index = ei

        raw = ffi.wasmtime_component_func_t()
        found = ffi.wasmtime_component_instance_get_func(
            byref(self._instance),
            store._context(),
            index.ptr(),
            byref(raw))
        if found:
            return Func._from_raw(raw)
        return None
