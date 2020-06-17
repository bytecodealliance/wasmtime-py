from . import _ffi as ffi
from ctypes import *
import typing


class ValType:
    @classmethod
    def i32(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_I32)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def i64(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_I64)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def f32(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_F32)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def f64(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_F64)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def anyref(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_ANYREF)
        return ValType.__from_ptr__(ptr, None)

    @classmethod
    def funcref(cls):
        ptr = ffi.wasm_valtype_new(ffi.WASM_FUNCREF)
        return ValType.__from_ptr__(ptr, None)

    def __init__(self):
        raise WasmtimeError("cannot construct directly")

    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner) -> "ValType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_valtype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    def __eq__(self, other: "ValType"):
        if not isinstance(other, ValType):
            return False
        assert(self.__ptr__ is not None)
        assert(other.__ptr__ is not None)
        kind1 = ffi.wasm_valtype_kind(self.__ptr__)
        kind2 = ffi.wasm_valtype_kind(other.__ptr__)
        return kind1 == kind2

    def __ne__(self, other: "ValType"):
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        assert(self.__ptr__ is not None)
        kind = ffi.wasm_valtype_kind(self.__ptr__)
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
            ffi.wasm_valtype_delete(self.__ptr__)

    @classmethod
    def __from_list__(cls, items: "P_wasm_valtype_vec_t", owner) -> typing.List["ValType"]:
        types = []
        for i in range(0, items.contents.size):
            types.append(ValType.__from_ptr__(items.contents.data[i], owner))
        return types


def take_owned_valtype(ty: ValType) -> pointer:
    if not isinstance(ty, ValType):
        raise TypeError("expected valtype")

    # Need to allocate a new type because we need to take ownership.
    #
    # Trying to expose this as an implementation detail by sneaking out
    # types and having some be "taken" feels pretty weird
    return ffi.wasm_valtype_new(ffi.wasm_valtype_kind(ty.__ptr__))


class FuncType:
    def __init__(self, params: typing.List[ValType], results: typing.List[ValType]):
        for param in params:
            if not isinstance(param, ValType):
                raise TypeError("expected ValType")
        for result in results:
            if not isinstance(result, ValType):
                raise TypeError("expected ValType")

        params_ffi = ffi.wasm_valtype_vec_t()
        ffi.wasm_valtype_vec_new_uninitialized(byref(params_ffi), len(params))

        results_ffi = ffi.wasm_valtype_vec_t()
        for i, param in enumerate(params):
            params_ffi.data[i] = take_owned_valtype(param)

        ffi.wasm_valtype_vec_new_uninitialized(
            byref(results_ffi), len(results))
        for i, result in enumerate(results):
            results_ffi.data[i] = take_owned_valtype(result)
        ptr = ffi.wasm_functype_new(byref(params_ffi), byref(results_ffi))
        if not ptr:
            raise WasmtimeError("failed to allocate FuncType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner) -> "FuncType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_functype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def params(self) -> typing.List["ValType"]:
        """
        Returns the list of parameter types for this function type
        """

        ptr = ffi.wasm_functype_params(self.__ptr__)
        return ValType.__from_list__(ptr, self)

    @property
    def results(self) -> typing.List["ValType"]:
        """
        Returns the list of result types for this function type
        """

        ptr = ffi.wasm_functype_results(self.__ptr__)
        return ValType.__from_list__(ptr, self)

    def _as_extern(self):
        return ffi.wasm_functype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_functype_delete(self.__ptr__)


class GlobalType:
    def __init__(self, valtype: ValType, mutable: bool):
        if mutable:
            mutability = ffi.WASM_VAR
        else:
            mutability = ffi.WASM_CONST
        type_ptr = take_owned_valtype(valtype)
        ptr = ffi.wasm_globaltype_new(type_ptr, mutability)
        if ptr == 0:
            raise WasmtimeError("failed to allocate GlobalType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner) -> "GlobalType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_globaltype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def content(self) -> ValType:
        """
        Returns the type this global contains
        """

        ptr = ffi.wasm_globaltype_content(self.__ptr__)
        return ValType.__from_ptr__(ptr, self)

    @property
    def mutable(self) -> bool:
        """
        Returns whether this global is mutable or not
        """
        val = ffi.wasm_globaltype_mutability(self.__ptr__)
        return val == ffi.WASM_VAR.value

    def _as_extern(self):
        return ffi.wasm_globaltype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_globaltype_delete(self.__ptr__)


class Limits:
    def __init__(self, min: int, max: typing.Optional[int]):
        self.min = min
        self.max = max

    def __ffi__(self) -> ffi.wasm_limits_t:
        max = self.max
        if max is None:
            max = 0xffffffff
        return ffi.wasm_limits_t(self.min, max)

    def __eq__(self, other: "Limits"):
        return self.min == other.min and self.max == other.max

    @classmethod
    def __from_ffi__(cls, val: pointer):
        min = val.contents.min
        max = val.contents.max
        if max == 0xffffffff:
            max = None
        return Limits(min, max)


class TableType:
    def __init__(self, valtype: ValType, limits: Limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        type_ptr = take_owned_valtype(valtype)
        ptr = ffi.wasm_tabletype_new(type_ptr, byref(limits.__ffi__()))
        if not ptr:
            raise WasmtimeError("failed to allocate TableType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner) -> "TableType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_tabletype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def element(self) -> ValType:
        """
        Returns the type of this table's elements
        """
        ptr = ffi.wasm_tabletype_element(self.__ptr__)
        return ValType.__from_ptr__(ptr, self)

    @property
    def limits(self) -> Limits:
        """
        Returns the limits on the size of thi stable
        """
        val = ffi.wasm_tabletype_limits(self.__ptr__)
        return Limits.__from_ffi__(val)

    def _as_extern(self):
        return ffi.wasm_tabletype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_tabletype_delete(self.__ptr__)


class MemoryType:
    def __init__(self, limits: Limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        ptr = ffi.wasm_memorytype_new(byref(limits.__ffi__()))
        if not ptr:
            raise WasmtimeError("failed to allocate MemoryType")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner) -> "MemoryType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_memorytype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def limits(self) -> Limits:
        """
        Returns the limits on the size of this table
        """
        val = ffi.wasm_memorytype_limits(self.__ptr__)
        return Limits.__from_ffi__(val)

    def _as_extern(self):
        return ffi.wasm_memorytype_as_externtype_const(self.__ptr__)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            ffi.wasm_memorytype_delete(self.__ptr__)


def wrap_externtype(ptr, owner):
    if not isinstance(ptr, POINTER(ffi.wasm_externtype_t)):
        raise TypeError("wrong pointer type")
    val = ffi.wasm_externtype_as_functype_const(ptr)
    if val:
        return FuncType.__from_ptr__(val, owner)
    val = ffi.wasm_externtype_as_tabletype_const(ptr)
    if val:
        return TableType.__from_ptr__(val, owner)
    val = ffi.wasm_externtype_as_globaltype_const(ptr)
    if val:
        return GlobalType.__from_ptr__(val, owner)
    val = ffi.wasm_externtype_as_memorytype_const(ptr)
    assert(val)
    return MemoryType.__from_ptr__(val, owner)


class ImportType:
    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner) -> "ImportType":
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_importtype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def module(self) -> str:
        """
        Returns the module this import type refers to
        """

        return ffi.to_str(ffi.wasm_importtype_module(self.__ptr__).contents)

    @property
    def name(self) -> str:
        """
        Returns the name in the modulethis import type refers to
        """
        return ffi.to_str(ffi.wasm_importtype_name(self.__ptr__).contents)

    @property
    def type(self) -> "ExternalType":
        """
        Returns the type that this import refers to
        """
        ptr = ffi.wasm_importtype_type(self.__ptr__)
        return wrap_externtype(ptr, self.__owner__ or self)

    def __del__(self):
        if self.__owner__ is None:
            ffi.wasm_importtype_delete(self.__ptr__)


class ExportType:
    @classmethod
    def __from_ptr__(cls, ptr: pointer, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_exporttype_t)):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    @property
    def name(self) -> str:
        """
        Returns the name in the modulethis export type refers to
        """
        return ffi.to_str(ffi.wasm_exporttype_name(self.__ptr__).contents)

    @property
    def type(self) -> "ExternalType":
        """
        Returns the type that this export refers to
        """
        ptr = ffi.wasm_exporttype_type(self.__ptr__)
        return wrap_externtype(ptr, self.__owner__ or self)

    def __del__(self):
        if self.__owner__ is None:
            ffi.wasm_exporttype_delete(self.__ptr__)


ExternalType = typing.Union[FuncType, TableType, MemoryType, GlobalType]
