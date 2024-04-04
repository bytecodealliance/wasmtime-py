from . import _ffi as ffi
from wasmtime import WasmtimeError, Managed
import ctypes
from ctypes import byref, POINTER
from typing import Union, List, Optional, Any


class ValType(Managed["ctypes._Pointer[ffi.wasm_valtype_t]"]):
    _owner: Optional[Any]

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_valtype_t]") -> None:
        # If this is owned by another object we don't free it since that object
        # is responsible for freeing the backing memory.
        if self._owner is None:
            ffi.wasm_valtype_delete(ptr)

    @classmethod
    def i32(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_I32)
        return ValType._from_ptr(ptr, None)

    @classmethod
    def i64(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_I64)
        return ValType._from_ptr(ptr, None)

    @classmethod
    def f32(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_F32)
        return ValType._from_ptr(ptr, None)

    @classmethod
    def f64(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_F64)
        return ValType._from_ptr(ptr, None)

    @classmethod
    def externref(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_ANYREF)
        return ValType._from_ptr(ptr, None)

    @classmethod
    def funcref(cls) -> "ValType":
        ptr = ffi.wasm_valtype_new(ffi.WASM_FUNCREF)
        return ValType._from_ptr(ptr, None)

    def __init__(self) -> None:
        raise WasmtimeError("cannot construct directly")

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_valtype_t]", owner: Optional[Any]) -> "ValType":
        if not isinstance(ptr, POINTER(ffi.wasm_valtype_t)):
            raise TypeError("wrong pointer type")
        ty: "ValType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValType):
            return False
        kind1 = ffi.wasm_valtype_kind(self.ptr())
        kind2 = ffi.wasm_valtype_kind(other.ptr())
        return kind1 == kind2

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        kind = ffi.wasm_valtype_kind(self.ptr())
        if kind == ffi.WASM_I32.value:
            return 'i32'
        if kind == ffi.WASM_I64.value:
            return 'i64'
        if kind == ffi.WASM_F32.value:
            return 'f32'
        if kind == ffi.WASM_F64.value:
            return 'f64'
        if kind == ffi.WASM_ANYREF.value:
            return 'anyref'
        if kind == ffi.WASM_FUNCREF.value:
            return 'funcref'
        return 'ValType(%d)' % kind.value

    @classmethod
    def _from_list(cls, items: "ctypes._Pointer[ffi.wasm_valtype_vec_t]", owner: Optional[Any]) -> List["ValType"]:
        types = []
        for i in range(0, items.contents.size):
            types.append(ValType._from_ptr(items.contents.data[i], owner))
        return types


def take_owned_valtype(ty: ValType) -> "ctypes._Pointer[ffi.wasm_valtype_t]":
    if not isinstance(ty, ValType):
        raise TypeError("expected valtype")

    # Need to allocate a new type because we need to take ownership.
    #
    # Trying to expose this as an implementation detail by sneaking out
    # types and having some be "taken" feels pretty weird
    return ffi.wasm_valtype_new(ffi.wasm_valtype_kind(ty.ptr()))


class FuncType(Managed["ctypes._Pointer[ffi.wasm_functype_t]"]):
    def __init__(self, params: List[ValType], results: List[ValType]):
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
        self._set_ptr(ptr)
        self._owner = None

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_functype_t]") -> None:
        if self._owner is None:
            ffi.wasm_functype_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_functype_t]", owner: Optional[Any]) -> "FuncType":
        if not isinstance(ptr, POINTER(ffi.wasm_functype_t)):
            raise TypeError("wrong pointer type")
        ty: "FuncType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    @property
    def params(self) -> List["ValType"]:
        """
        Returns the list of parameter types for this function type
        """

        ptr = ffi.wasm_functype_params(self.ptr())
        return ValType._from_list(ptr, self)

    @property
    def results(self) -> List["ValType"]:
        """
        Returns the list of result types for this function type
        """

        ptr = ffi.wasm_functype_results(self.ptr())
        return ValType._from_list(ptr, self)

    def _as_extern(self) -> "ctypes._Pointer[ffi.wasm_externtype_t]":
        return ffi.wasm_functype_as_externtype_const(self.ptr())


class GlobalType(Managed["ctypes._Pointer[ffi.wasm_globaltype_t]"]):
    def __init__(self, valtype: ValType, mutable: bool):
        if mutable:
            mutability = ffi.WASM_VAR
        else:
            mutability = ffi.WASM_CONST
        type_ptr = take_owned_valtype(valtype)
        ptr = ffi.wasm_globaltype_new(type_ptr, mutability)
        if ptr == 0:
            raise WasmtimeError("failed to allocate GlobalType")
        self._set_ptr(ptr)
        self._owner = None

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_globaltype_t]") -> None:
        if self._owner is None:
            ffi.wasm_globaltype_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_globaltype_t]", owner: Optional[Any]) -> "GlobalType":
        if not isinstance(ptr, POINTER(ffi.wasm_globaltype_t)):
            raise TypeError("wrong pointer type")
        ty: "GlobalType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    @property
    def content(self) -> ValType:
        """
        Returns the type this global contains
        """

        ptr = ffi.wasm_globaltype_content(self.ptr())
        return ValType._from_ptr(ptr, self)

    @property
    def mutable(self) -> bool:
        """
        Returns whether this global is mutable or not
        """
        val = ffi.wasm_globaltype_mutability(self.ptr())
        return val == ffi.WASM_VAR.value

    def _as_extern(self) -> "ctypes._Pointer[ffi.wasm_externtype_t]":
        return ffi.wasm_globaltype_as_externtype_const(self.ptr())


class Limits:
    def __init__(self, min: int, max: Optional[int]):
        self.min = min
        self.max = max

    def __ffi__(self) -> ffi.wasm_limits_t:
        max = self.max
        if max is None:
            max = 0xffffffff
        return ffi.wasm_limits_t(self.min, max)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Limits):
            return False
        return self.min == other.min and self.max == other.max

    @classmethod
    def _from_ffi(cls, val: 'ctypes._Pointer[ffi.wasm_limits_t]') -> "Limits":
        min = val.contents.min
        max = val.contents.max
        if max == 0xffffffff:
            return Limits(min, None)
        return Limits(min, max)


class TableType(Managed["ctypes._Pointer[ffi.wasm_tabletype_t]"]):
    def __init__(self, valtype: ValType, limits: Limits):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        type_ptr = take_owned_valtype(valtype)
        ptr = ffi.wasm_tabletype_new(type_ptr, byref(limits.__ffi__()))
        if not ptr:
            raise WasmtimeError("failed to allocate TableType")
        self._set_ptr(ptr)
        self._owner = None

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_tabletype_t]") -> None:
        if self._owner is None:
            ffi.wasm_tabletype_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: 'ctypes._Pointer[ffi.wasm_tabletype_t]', owner: Optional[Any]) -> "TableType":
        ty: "TableType" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_tabletype_t)):
            raise TypeError("wrong pointer type")
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    @property
    def element(self) -> ValType:
        """
        Returns the type of this table's elements
        """
        ptr = ffi.wasm_tabletype_element(self.ptr())
        return ValType._from_ptr(ptr, self)

    @property
    def limits(self) -> Limits:
        """
        Returns the limits on the size of thi stable
        """
        val = ffi.wasm_tabletype_limits(self.ptr())
        return Limits._from_ffi(val)

    def _as_extern(self) -> "ctypes._Pointer[ffi.wasm_externtype_t]":
        return ffi.wasm_tabletype_as_externtype_const(self.ptr())


class MemoryType(Managed["ctypes._Pointer[ffi.wasm_memorytype_t]"]):
    def __init__(self, limits: Limits, is_64: bool = False):
        if not isinstance(limits, Limits):
            raise TypeError("expected Limits")
        if is_64:
            maximum = 0x10000000000000000
        else:
            maximum = 0x100000000
        if limits.min >= maximum:
            raise WasmtimeError("minimum size too large")
        if limits.max and limits.max >= maximum:
            raise WasmtimeError("maximum size too large")
        ptr = ffi.wasmtime_memorytype_new(limits.min,
                                          limits.max is not None,
                                          limits.max if limits.max else 0,
                                          is_64)
        if not ptr:
            raise WasmtimeError("failed to allocate MemoryType")
        self._set_ptr(ptr)
        self._owner = None

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_memorytype_t]") -> None:
        if self._owner is None:
            ffi.wasm_memorytype_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_memorytype_t]", owner: Optional[Any]) -> "MemoryType":
        if not isinstance(ptr, POINTER(ffi.wasm_memorytype_t)):
            raise TypeError("wrong pointer type")
        ty: "MemoryType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    @property
    def limits(self) -> Limits:
        """
        Returns the limits on the size of this table
        """
        minimum = ffi.wasmtime_memorytype_minimum(self.ptr())
        maximum = ffi.c_uint64(0)
        has_max = ffi.wasmtime_memorytype_maximum(self.ptr(), byref(maximum))
        return Limits(minimum, maximum.value if has_max else None)

    @property
    def is_64(self) -> bool:
        """
        Returns whether or not this is a 64-bit memory
        """
        return ffi.wasmtime_memorytype_is64(self.ptr())

    def _as_extern(self) -> "ctypes._Pointer[ffi.wasm_externtype_t]":
        return ffi.wasm_memorytype_as_externtype_const(self.ptr())


def wrap_externtype(ptr: "ctypes._Pointer[ffi.wasm_externtype_t]", owner: Optional[Any]) -> "AsExternType":
    if not isinstance(ptr, POINTER(ffi.wasm_externtype_t)):
        raise TypeError("wrong pointer type")
    val = ffi.wasm_externtype_as_functype(ptr)
    if val:
        return FuncType._from_ptr(val, owner)
    val = ffi.wasm_externtype_as_tabletype(ptr)
    if val:
        return TableType._from_ptr(val, owner)
    val = ffi.wasm_externtype_as_globaltype(ptr)
    if val:
        return GlobalType._from_ptr(val, owner)
    val = ffi.wasm_externtype_as_memorytype(ptr)
    if val:
        return MemoryType._from_ptr(val, owner)
    raise WasmtimeError("unknown extern type")


class ImportType(Managed["ctypes._Pointer[ffi.wasm_importtype_t]"]):
    _owner: Optional[Any]

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasm_importtype_t]", owner: Optional[Any]) -> "ImportType":
        if not isinstance(ptr, POINTER(ffi.wasm_importtype_t)):
            raise TypeError("wrong pointer type")
        ty: "ImportType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_importtype_t]") -> None:
        if self._owner is None:
            ffi.wasm_importtype_delete(ptr)

    @property
    def module(self) -> str:
        """
        Returns the module this import type refers to
        """

        return ffi.to_str(ffi.wasm_importtype_module(self.ptr()).contents)

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name in the module this import type refers to

        Note that `None` may be returned for the module linking proposal where
        the field name is optional.
        """
        ptr = ffi.wasm_importtype_name(self.ptr())
        if ptr:
            return ffi.to_str(ptr.contents)
        return None

    @property
    def type(self) -> "AsExternType":
        """
        Returns the type that this import refers to
        """
        ptr = ffi.wasm_importtype_type(self.ptr())
        return wrap_externtype(ptr, self._owner or self)


class ExportType(Managed["ctypes._Pointer[ffi.wasm_exporttype_t]"]):
    _ptr: "ctypes._Pointer[ffi.wasm_exporttype_t]"
    _owner: Optional[Any]

    @classmethod
    def _from_ptr(cls, ptr: 'ctypes._Pointer[ffi.wasm_exporttype_t]', owner: Optional[Any]) -> "ExportType":
        if not isinstance(ptr, POINTER(ffi.wasm_exporttype_t)):
            raise TypeError("wrong pointer type")
        ty: "ExportType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasm_exporttype_t]") -> None:
        if self._owner is None:
            ffi.wasm_exporttype_delete(ptr)

    @property
    def name(self) -> str:
        """
        Returns the name in the modulethis export type refers to
        """
        return ffi.to_str(ffi.wasm_exporttype_name(self.ptr()).contents)

    @property
    def type(self) -> "AsExternType":
        """
        Returns the type that this export refers to
        """
        ptr = ffi.wasm_exporttype_type(self.ptr())
        return wrap_externtype(ptr, self._owner or self)


AsExternType = Union[FuncType, TableType, MemoryType, GlobalType]
