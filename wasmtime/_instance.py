from ._ffi import *
from ctypes import *
from wasmtime import Module, Extern, Func, Table, Memory, Trap, Global, WasmtimeError

dll.wasmtime_instance_new.restype = P_wasmtime_error_t


class Instance(object):
    def __init__(self, module, imports):
        """
        Creates a new instance by instantiating the `module` given with the
        `imports` provided.

        The `module` must have type `Module`, and the `imports` must be an
        iterable of external values, either `Extern`, `Func`, `Table`, `Memory`,
        or `Global`.

        Raises an error if instantiation fails (e.g. linking or trap) and
        otherwise initializes the new instance.
        """

        if not isinstance(module, Module):
            raise TypeError("expected a Module")

        imports_ptr = (P_wasm_extern_t * len(imports))()
        for i, val in enumerate(imports):
            if isinstance(val, Extern):
                imports_ptr[i] = val.__ptr__
            elif isinstance(val, Func):
                imports_ptr[i] = val.as_extern().__ptr__
            elif isinstance(val, Memory):
                imports_ptr[i] = val.as_extern().__ptr__
            elif isinstance(val, Global):
                imports_ptr[i] = val.as_extern().__ptr__
            elif isinstance(val, Table):
                imports_ptr[i] = val.as_extern().__ptr__
            else:
                raise TypeError("expected an external item as an import")

        instance = P_wasm_instance_t()
        trap = P_wasm_trap_t()
        error = dll.wasmtime_instance_new(
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

    @classmethod
    def __from_ptr__(cls, ptr, module):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_instance_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty._module = module
        return ty

    def exports(self):
        """
        Returns the exports of this module
        """
        externs = ExternTypeList()
        dll.wasm_instance_exports(self.__ptr__, byref(externs.vec))
        ret = []
        for i in range(0, externs.vec.size):
            ret.append(Extern.__from_ptr__(externs.vec.data[i], externs))
        return ret

    def get_export(self, name):
        """
        Gets an export from this module by name, returning `None` if the name
        doesn't exist.
        """
        if not hasattr(self, '_export_map'):
            self._export_map = {}
            exports = self.exports()
            for i, export in enumerate(self._module.exports()):
                self._export_map[export.name()] = exports[i]
        if name in self._export_map:
            return self._export_map[name]
        else:
            return None

    def __del__(self):
        if hasattr(self, '__ptr__'):
            dll.wasm_instance_delete(self.__ptr__)


class ExternTypeList(object):
    def __init__(self):
        self.vec = wasm_extern_vec_t(0, None)

    def __del__(self):
        dll.wasm_extern_vec_delete(byref(self.vec))
