from .ffi import *
from ctypes import *

class ValType:
    @classmethod
    def i32(cls):
        ptr = dll.wasm_valtype_new(WASM_I32)
        return cls(cast(ptr, P_wasm_valtype_t))

    @classmethod
    def i64(cls):
        ptr = dll.wasm_valtype_new(WASM_I64)
        return cls(cast(ptr, P_wasm_valtype_t))

    @classmethod
    def f32(cls):
        ptr = dll.wasm_valtype_new(WASM_F32)
        return cls(cast(ptr, P_wasm_valtype_t))

    @classmethod
    def f64(cls):
        ptr = dll.wasm_valtype_new(WASM_F64)
        return cls(cast(ptr, P_wasm_valtype_t))

    def __init__(self, ptr):
        if ptr == 0:
            raise RuntimeError("failed to allocate ValType")
        if not isinstance(ptr, P_wasm_valtype_t):
            raise RuntimeError("wrong pointer type")
        self.__ptr__ = ptr
        self.__owner__ = None

    def __eq__(self, other):
        if not isinstance(other, ValType):
            return False
        return dll.wasm_valtype_kind(self.__ptr__) == dll.wasm_valtype_kind(other.__ptr__)

    def __repr__(self):
        return str(self)

    def __str__(self):
        kind = c_uint8(dll.wasm_valtype_kind(self.__ptr__)).value
        if kind == WASM_I32.value:
            return 'i32'
        if kind == WASM_I64.value:
            return 'i64'
        if kind == WASM_F32.value:
            return 'f32'
        if kind == WASM_F64.value:
            return 'f64'
        return 'ValType(%d)' % kind

    def __del__(self):
        # If this is owned by another object we don't free it since that object
        # is responsible for freeing the backing memory.
        if self.__owner__ is None and self.__ptr__ is not None:
            dll.wasm_valtype_delete(self.__ptr__)

    @classmethod
    def __from_list__(cls, items, owner):
        types = []
        for i in range(0, items.contents.size):
            val = ValType(items.contents.data[i])
            val.__owner__ = owner
            types.append(val)
        return types


class FuncType:
    def __init__(self, params, results):
        params_ffi = wasm_valtype_vec_t()
        dll.wasm_valtype_vec_new_uninitialized(byref(params_ffi), len(params))
        results_ffi = wasm_valtype_vec_t()
        for i, param in enumerate(params):
            params_ffi.data[i] = param.__ptr__
        dll.wasm_valtype_vec_new_uninitialized(byref(results_ffi), len(results))
        for i, result in enumerate(results):
            results_ffi.data[i] = result.__ptr__
        ptr = dll.wasm_functype_new(byref(params_ffi), byref(results_ffi))
        if ptr == 0:
            raise RuntimeError("failed to allocate ValType")
        self.__ptr__ = cast(ptr, P_wasm_functype_t)

    # Returns the list of parameter types for this function type
    def params(self):
        ptr = cast(dll.wasm_functype_params(self.__ptr__), POINTER(wasm_valtype_vec_t))
        return ValType.__from_list__(ptr, self)

    # Returns the list of result types for this function type
    def results(self):
        ptr = cast(dll.wasm_functype_results(self.__ptr__), POINTER(wasm_valtype_vec_t))
        return ValType.__from_list__(ptr, self)

    def __del__(self):
        dll.wasm_functype_delete(self.__ptr__)

class GlobalType:
    def __init__(self, valtype, mutable):
        if not isinstance(valtype, ValType):
            raise RuntimeError("expected valtype")
        if not isinstance(mutable, bool):
            raise RuntimeError("expected valtype")
        if mutable:
            mutability = WASM_VAR
        else:
            mutability = WASM_CONST
        type_ptr = valtype.__ptr__
        valtype.__ptr__ = None
        ptr = dll.wasm_globaltype_new(type_ptr, mutability)
        if ptr == 0:
            raise RuntimeError("failed to allocate ValType")
        self.__ptr__ = cast(ptr, P_wasm_globaltype_t)

    # Returns the type this global contains
    def content(self):
        ptr = cast(dll.wasm_globaltype_content(self.__ptr__), POINTER(wasm_valtype_t))
        ty = ValType(ptr)
        ty.__owner__ = self
        return ty

    # Returns whether this global is mutable or not
    def mutable(self):
        val = c_uint8(dll.wasm_globaltype_mutability(self.__ptr__))
        return val.value == WASM_VAR.value

    def __del__(self):
        dll.wasm_globaltype_delete(self.__ptr__)
