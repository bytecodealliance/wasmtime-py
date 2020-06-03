from ._ffi import *
from ctypes import *
from wasmtime import Module, Trap, WasmtimeError, Store
from ._extern import wrap_extern, get_extern_ptr

dll.wasmtime_instance_new.restype = P_wasmtime_error_t


class Instance:
    def __init__(self, store, module, imports):
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

        imports_ptr = (P_wasm_extern_t * len(imports))()
        for i, val in enumerate(imports):
            imports_ptr[i] = get_extern_ptr(val)

        instance = P_wasm_instance_t()
        trap = P_wasm_trap_t()
        error = dll.wasmtime_instance_new(
            store.__ptr__,
            module.__ptr__,
            imports_ptr,
            len(imports),
            byref(instance),
            byref(trap))
        if error:
            raise WasmtimeError.__from_ptr__(error)
        if trap:
            raise Trap.__from_ptr__(trap)
        self.__ptr__ = instance
        self._module = module
        self._exports = None

    @classmethod
    def __from_ptr__(cls, ptr, module):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_instance_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty._module = module
        ty._exports = None
        return ty

    @property
    def exports(self):
        """
        Returns the exports of this module

        The returned type can be indexed both with integers and with strings for
        names of exports.
        """
        if self._exports is None:
            externs = ExternTypeList()
            dll.wasm_instance_exports(self.__ptr__, byref(externs.vec))
            extern_list = []
            for i in range(0, externs.vec.size):
                extern_list.append(wrap_extern(externs.vec.data[i], externs))
            self._exports = InstanceExports(extern_list, self._module)
        return self._exports

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_instance_delete(self.__ptr__)


class InstanceExports:
    def __init__(self, extern_list, module):
        self._extern_list = extern_list
        self._extern_map = {}
        exports = module.exports
        for i, extern in enumerate(extern_list):
            self._extern_map[exports[i].name] = extern

    def __getitem__(self, idx):
        ret = self.get(idx)
        if ret is None:
            msg = "failed to find export {}".format(idx)
            if isinstance(idx, str):
                raise KeyError(msg)
            raise IndexError(msg)
        return ret

    def __len__(self):
        return len(self._extern_list)

    def __iter__(self):
        return iter(self._extern_list)

    def get(self, idx):
        if isinstance(idx, str):
            return self._extern_map.get(idx)
        if idx < len(self._extern_list):
            return self._extern_list[idx]
        return None


class ExternTypeList:
    def __init__(self):
        self.vec = wasm_extern_vec_t(0, None)

    def __del__(self):
        dll.wasm_extern_vec_delete(byref(self.vec))
