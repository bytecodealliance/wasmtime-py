from .ffi import *
from ctypes import *

class ValType:
    @classmethod
    def i32(cls):
        ptr = dll.wasm_valtype_new(WASM_I32)
        return ValType.__from_ptr__(cast(ptr, P_wasm_valtype_t), None)

    @classmethod
    def i64(cls):
        ptr = dll.wasm_valtype_new(WASM_I64)
        return ValType.__from_ptr__(cast(ptr, P_wasm_valtype_t), None)

    @classmethod
    def f32(cls):
        ptr = dll.wasm_valtype_new(WASM_F32)
        return ValType.__from_ptr__(cast(ptr, P_wasm_valtype_t), None)

    @classmethod
    def f64(cls):
        ptr = dll.wasm_valtype_new(WASM_F64)
        return ValType.__from_ptr__(cast(ptr, P_wasm_valtype_t), None)

    def __init__(self):
        raise RuntimeError("cannot construct directly")

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_valtype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    def __eq__(self, other):
        if not isinstance(other, ValType):
            return False
        assert(self.__ptr__ is not None)
        assert(other.__ptr__ is not None)
        return dll.wasm_valtype_kind(self.__ptr__) == dll.wasm_valtype_kind(other.__ptr__)

    def __repr__(self):
        return str(self)

    def __str__(self):
        assert(self.__ptr__ is not None)
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
        if not hasattr(self, '__owner__'):
            return
        # If this is owned by another object we don't free it since that object
        # is responsible for freeing the backing memory.
        if self.__owner__ is None and self.__ptr__ is not None:
            dll.wasm_valtype_delete(self.__ptr__)

    @classmethod
    def __from_list__(cls, items, owner):
        types = []
        for i in range(0, items.contents.size):
            types.append(ValType.__from_ptr__(items.contents.data[i], owner))
        return types

def take_owned_valtype(ty):
    if not isinstance(ty, ValType):
        raise TypeError("expected valtype")
    elif ty.__owner__ is not None:
        raise RuntimeError("ValType owned by something else")
    elif ty.__ptr__ is None:
        raise RuntimeError("ValType already used up")
    type_ptr = ty.__ptr__
    ty.__ptr__ = None
    return type_ptr

class FuncType:
    def __init__(self, params, results):
        for param in params:
            if not isinstance(param, ValType):
                raise TypeError("expected ValType")
            elif param.__ptr__ is None:
                raise RuntimeError("ValType already used up")
        for result in results:
            if not isinstance(param, ValType):
                raise TypeError("expected ValType")
            elif result.__ptr__ is None:
                raise RuntimeError("ValType already used up")

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
            raise RuntimeError("failed to allocate FuncType")
        self.__ptr__ = cast(ptr, P_wasm_functype_t)
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_functype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Returns the list of parameter types for this function type
    def params(self):
        ptr = cast(dll.wasm_functype_params(self.__ptr__), POINTER(wasm_valtype_vec_t))
        return ValType.__from_list__(ptr, self)

    # Returns the list of result types for this function type
    def results(self):
        ptr = cast(dll.wasm_functype_results(self.__ptr__), POINTER(wasm_valtype_vec_t))
        return ValType.__from_list__(ptr, self)

    # # Returns this type as an `ExternType` instance
    # def as_extern(self):
    #     ptr = cast(dll.wasm_functype_as_externtype(self.__ptr__), P_wasm_externtype_t)
    #     return ExternType(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_functype_delete(self.__ptr__)

class GlobalType:
    def __init__(self, valtype, mutable):
        if mutable:
            mutability = WASM_VAR
        else:
            mutability = WASM_CONST
        type_ptr = take_owned_valtype(valtype)
        ptr = dll.wasm_globaltype_new(type_ptr, mutability)
        if ptr == 0:
            raise RuntimeError("failed to allocate GlobalType")
        self.__ptr__ = cast(ptr, P_wasm_globaltype_t)
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_globaltype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Returns the type this global contains
    def content(self):
        ptr = cast(dll.wasm_globaltype_content(self.__ptr__), POINTER(wasm_valtype_t))
        return ValType.__from_ptr__(ptr, self)

    # Returns whether this global is mutable or not
    def mutable(self):
        val = c_uint8(dll.wasm_globaltype_mutability(self.__ptr__))
        return val.value == WASM_VAR.value

    # # Returns this type as an `ExternType` instance
    # def as_extern(self):
    #     ptr = cast(dll.wasm_globaltype_as_externtype(self.__ptr__), P_wasm_externtype_t)
    #     return ExternType(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_globaltype_delete(self.__ptr__)

class Limits:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __ffi__(self):
        max = self.max
        if max is None:
            max = 0xffffffff
        return wasm_limits_t(self.min, max)

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    @classmethod
    def __from_ffi__(cls, val):
        min = val.contents.min
        max = val.contents.max
        if max == 0xffffffff:
            max = None
        return Limits(min, max)

class TableType:
    def __init__(self, valtype, limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        type_ptr = take_owned_valtype(valtype)
        ptr = dll.wasm_tabletype_new(type_ptr, byref(limits.__ffi__()))
        if ptr == 0:
            raise RuntimeError("failed to allocate TableType")
        self.__ptr__ = cast(ptr, P_wasm_tabletype_t)
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_tabletype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Returns the type of this table's elements
    def element(self):
        ptr = cast(dll.wasm_tabletype_element(self.__ptr__), POINTER(wasm_valtype_t))
        return ValType.__from_ptr__(ptr, self)

    # Returns the limits on the size of thi stable
    def limits(self):
        val = cast(dll.wasm_tabletype_limits(self.__ptr__), POINTER(wasm_limits_t))
        return Limits.__from_ffi__(val)

    # # Returns this type as an `ExternType` instance
    # def as_extern(self):
    #     ptr = cast(dll.wasm_tabletype_as_externtype(self.__ptr__), P_wasm_externtype_t)
    #     return ExternType(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_tabletype_delete(self.__ptr__)

class MemoryType:
    def __init__(self, limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        ptr = dll.wasm_memorytype_new(byref(limits.__ffi__()))
        if ptr == 0:
            raise RuntimeError("failed to allocate MemoryType")
        self.__ptr__ = cast(ptr, P_wasm_memorytype_t)
        self.__owner__ = None

    # Returns the limits on the size of thi stable
    def limits(self):
        val = cast(dll.wasm_memorytype_limits(self.__ptr__), POINTER(wasm_limits_t))
        return Limits.__from_ffi__(val)

    # # Returns this type as an `ExternType` instance
    # def as_extern(self):
    #     ptr = cast(dll.wasm_memorytype_as_externtype(self.__ptr__), P_wasm_externtype_t)
    #     return ExternType(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_memorytype_delete(self.__ptr__)

class ExternType:
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_externtype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Returns this type as a `FuncType` or `None` if it's not a function
    def func_type(self):
        val = cast(dll.wasm_externtype_as_functype_const(self.__ptr__), P_wasm_functype_t)
        if val:
            return FuncType.__from_ptr__(val, self.__owner__ or self)
        else:
            return None

    # Returns this type as a `TableType` or `None` if it's not a table
    def table_type(self):
        val = cast(dll.wasm_externtype_as_tabletype_const(self.__ptr__), P_wasm_tabletype_t)
        if val:
            return TableType.__from_ptr__(val, self.__owner__ or self)
        else:
            return None

    # Returns this type as a `GlobalType` or `None` if it's not a global
    def global_type(self):
        val = cast(dll.wasm_externtype_as_globaltype_const(self.__ptr__), P_wasm_globaltype_t)
        if val:
            return GlobalType.__from_ptr__(val, self.__owner__ or self)
        else:
            return None

    # Returns this type as a `MemoryType` or `None` if it's not a memory
    def memory_type(self):
        val = cast(dll.wasm_externtype_as_memorytype_const(self.__ptr__), P_wasm_memorytype_t)
        if val:
            return MemoryType.__from_ptr__(val, self.__owner__ or self)
        else:
            return None

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_externtype_delete(self.__ptr__)

class ImportType:
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_importtype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # # Returns the module name this import type refers to
    # def module(self):
    #     val = cast(dll.wasm_importtype_module(self.__ptr__), POINTER(wasm_name_t))
    #     if val:
    #         return FuncType.__from_ptr__(val, self.__owner__ or self)
    #     else:
    #         return None

    def __del__(self):
        if self.__owner__ is None:
            dll.wasm_importtype_delete(self.__ptr__)
