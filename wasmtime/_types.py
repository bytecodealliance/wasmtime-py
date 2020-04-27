from ._ffi import *
from ctypes import *

dll.wasm_valtype_new.restype = P_wasm_valtype_t
dll.wasm_functype_new.restype = P_wasm_functype_t
dll.wasm_functype_params.restype = POINTER(wasm_valtype_vec_t)
dll.wasm_functype_results.restype = POINTER(wasm_valtype_vec_t)
dll.wasm_globaltype_new.restype = P_wasm_globaltype_t
dll.wasm_globaltype_content.restype = P_wasm_valtype_t
dll.wasm_tabletype_new.restype = P_wasm_tabletype_t
dll.wasm_tabletype_element.restype = P_wasm_valtype_t
dll.wasm_tabletype_limits.restype = POINTER(wasm_limits_t)
dll.wasm_memorytype_new.restype = P_wasm_memorytype_t
dll.wasm_memorytype_limits.restype = POINTER(wasm_limits_t)
dll.wasm_externtype_as_functype_const.restype = P_wasm_functype_t
dll.wasm_externtype_as_tabletype_const.restype = P_wasm_tabletype_t
dll.wasm_externtype_as_memorytype_const.restype = P_wasm_memorytype_t
dll.wasm_externtype_as_globaltype_const.restype = P_wasm_globaltype_t
dll.wasm_importtype_module.restype = POINTER(wasm_name_t)
dll.wasm_importtype_name.restype = POINTER(wasm_name_t)
dll.wasm_importtype_type.restype = P_wasm_externtype_t
dll.wasm_exporttype_name.restype = POINTER(wasm_name_t)
dll.wasm_exporttype_type.restype = P_wasm_externtype_t
dll.wasm_memorytype_as_externtype_const.restype = P_wasm_externtype_t
dll.wasm_tabletype_as_externtype_const.restype = P_wasm_externtype_t
dll.wasm_globaltype_as_externtype_const.restype = P_wasm_externtype_t
dll.wasm_functype_as_externtype_const.restype = P_wasm_externtype_t

dll.wasm_valtype_kind.restype = c_uint8
dll.wasm_globaltype_mutability.restype = c_uint8


class ValType(object):
    @classmethod
    def i32(cls):
        ptr = dll.wasm_valtype_new(WASM_I32)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def i64(cls):
        ptr = dll.wasm_valtype_new(WASM_I64)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def f32(cls):
        ptr = dll.wasm_valtype_new(WASM_F32)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def f64(cls):
        ptr = dll.wasm_valtype_new(WASM_F64)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def anyref(cls):
        ptr = dll.wasm_valtype_new(WASM_ANYREF)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def funcref(cls):
        ptr = dll.wasm_valtype_new(WASM_FUNCREF)
        return ValType.__from_ptr__(ptr, None)

    def __init__(self):
        raise WasmtimeError("cannot construct directly")

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
        kind1 = dll.wasm_valtype_kind(self.__ptr__)
        kind2 = dll.wasm_valtype_kind(other.__ptr__)
        return kind1 == kind2

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        assert(self.__ptr__ is not None)
        kind = dll.wasm_valtype_kind(self.__ptr__)
        if kind == WASM_I32.value:
            return 'i32'
        if kind == WASM_I64.value:
            return 'i64'
        if kind == WASM_F32.value:
            return 'f32'
        if kind == WASM_F64.value:
            return 'f64'
        if kind == WASM_ANYREF.value:
            return 'anyref'
        if kind == WASM_FUNCREF.value:
            return 'funcref'
        return 'ValType(%d)' % kind

    def __del__(self):
        if not hasattr(self, '__owner__') or not hasattr(self, '__ptr__'):
            return
        # If this is owned by another object we don't free it since that object
        # is responsible for freeing the backing memory.
        if self.__owner__ is None:
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

    # Need to allocate a new type because we need to take ownership.
    #
    # Trying to expose this as an implementation detail by sneaking out
    # types and having some be "taken" feels pretty weird
    return dll.wasm_valtype_new(dll.wasm_valtype_kind(ty.__ptr__))


class FuncType(object):
    def __init__(self, params, results):
        for param in params:
            if not isinstance(param, ValType):
                raise TypeError("expected ValType")
        for result in results:
            if not isinstance(result, ValType):
                raise TypeError("expected ValType")

        params_ffi = wasm_valtype_vec_t()
        dll.wasm_valtype_vec_new_uninitialized(byref(params_ffi), len(params))

        results_ffi = wasm_valtype_vec_t()
        for i, param in enumerate(params):
            params_ffi.data[i] = take_owned_valtype(param)

        dll.wasm_valtype_vec_new_uninitialized(
            byref(results_ffi), len(results))
        for i, result in enumerate(results):
            results_ffi.data[i] = take_owned_valtype(result)
        ptr = dll.wasm_functype_new(byref(params_ffi), byref(results_ffi))
        if not ptr:
            raise WasmtimeError("failed to allocate FuncType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_functype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def params(self):
        """
        Returns the list of parameter types for this function type
        """

        ptr = dll.wasm_functype_params(self.__ptr__)
        return ValType.__from_list__(ptr, self)

    @property
    def results(self):
        """
        Returns the list of result types for this function type
        """

        ptr = dll.wasm_functype_results(self.__ptr__)
        return ValType.__from_list__(ptr, self)

    def _as_extern(self):
        return dll.wasm_functype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_functype_delete(self.__ptr__)


class GlobalType(object):
    def __init__(self, valtype, mutable):
        if mutable:
            mutability = WASM_VAR
        else:
            mutability = WASM_CONST
        type_ptr = take_owned_valtype(valtype)
        ptr = dll.wasm_globaltype_new(type_ptr, mutability)
        if ptr == 0:
            raise WasmtimeError("failed to allocate GlobalType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_globaltype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def content(self):
        """
        Returns the type this global contains
        """

        ptr = dll.wasm_globaltype_content(self.__ptr__)
        return ValType.__from_ptr__(ptr, self)

    @property
    def mutable(self):
        """
        Returns whether this global is mutable or not
        """
        val = dll.wasm_globaltype_mutability(self.__ptr__)
        return val == WASM_VAR.value

    def _as_extern(self):
        return dll.wasm_globaltype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_globaltype_delete(self.__ptr__)


class Limits(object):
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


class TableType(object):
    def __init__(self, valtype, limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        type_ptr = take_owned_valtype(valtype)
        ptr = dll.wasm_tabletype_new(type_ptr, byref(limits.__ffi__()))
        if not ptr:
            raise WasmtimeError("failed to allocate TableType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_tabletype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def element(self):
        """
        Returns the type of this table's elements
        """
        ptr = dll.wasm_tabletype_element(self.__ptr__)
        return ValType.__from_ptr__(ptr, self)

    @property
    def limits(self):
        """
        Returns the limits on the size of thi stable
        """
        val = dll.wasm_tabletype_limits(self.__ptr__)
        return Limits.__from_ffi__(val)

    def _as_extern(self):
        return dll.wasm_tabletype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_tabletype_delete(self.__ptr__)


class MemoryType(object):
    def __init__(self, limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        ptr = dll.wasm_memorytype_new(byref(limits.__ffi__()))
        if not ptr:
            raise WasmtimeError("failed to allocate MemoryType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_memorytype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def limits(self):
        """
        Returns the limits on the size of this table
        """
        val = dll.wasm_memorytype_limits(self.__ptr__)
        return Limits.__from_ffi__(val)

    def _as_extern(self):
        return dll.wasm_memorytype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_memorytype_delete(self.__ptr__)


def wrap_externtype(ptr, owner):
    if not isinstance(ptr, P_wasm_externtype_t):
        raise TypeError("wrong pointer type")
    val = dll.wasm_externtype_as_functype_const(ptr)
    if val:
        return FuncType.__from_ptr__(val, owner)
    val = dll.wasm_externtype_as_tabletype_const(ptr)
    if val:
        return TableType.__from_ptr__(val, owner)
    val = dll.wasm_externtype_as_globaltype_const(ptr)
    if val:
        return GlobalType.__from_ptr__(val, owner)
    val = dll.wasm_externtype_as_memorytype_const(ptr)
    assert(val)
    return MemoryType.__from_ptr__(val, owner)


class ImportType(object):
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_importtype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def module(self):
        """
        Returns the module this import type refers to
        """

        return dll.wasm_importtype_module(self.__ptr__).contents.to_str()

    @property
    def name(self):
        """
        Returns the name in the modulethis import type refers to
        """
        return dll.wasm_importtype_name(self.__ptr__).contents.to_str()

    @property
    def type(self):
        """
        Returns the type that this import refers to
        """
        ptr = dll.wasm_importtype_type(self.__ptr__)
        return wrap_externtype(ptr, self.__owner__ or self)

    def __del__(self):
        if self.__owner__ is None:
            dll.wasm_importtype_delete(self.__ptr__)


class ExportType(object):
    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_exporttype_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = cast(cast(ptr, c_void_p).value, P_wasm_exporttype_t)
        ty.__owner__ = owner
        return ty

    @property
    def name(self):
        """
        Returns the name in the modulethis export type refers to
        """
        return dll.wasm_exporttype_name(self.__ptr__).contents.to_str()

    @property
    def type(self):
        """
        Returns the type that this export refers to
        """
        ptr = dll.wasm_exporttype_type(self.__ptr__)
        return wrap_externtype(ptr, self.__owner__ or self)

    def __del__(self):
        if self.__owner__ is None:
            dll.wasm_exporttype_delete(self.__ptr__)
