from abc import abstractmethod
from .. import _ffi as ffi, ImportType, ExportType, WasmtimeError, Storelike
from ._resources import ResourceAny, ResourceHost
from ._resource_type import ResourceType
from dataclasses import dataclass
import ctypes
from ctypes import byref, POINTER
from typing import Any, Optional, Dict, List, Union, Tuple, Set
from wasmtime import Managed, Engine


class ComponentType(Managed["ctypes._Pointer[ffi.wasmtime_component_type_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ComponentType`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_type_t]") -> None:
        ffi.wasmtime_component_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_type_t]") -> "ComponentType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ComponentType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    def imports(self, engine: Engine) -> Dict[str, "ComponentItem"]:
        """
        Returns a dictionary of the imports of this component type.
        """
        n = ffi.wasmtime_component_type_import_count(self.ptr(), engine.ptr())
        items = {}
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            item = ffi.wasmtime_component_item_t()
            found = ffi.wasmtime_component_type_import_nth(self.ptr(),
                                                           engine.ptr(),
                                                           i,
                                                           byref(name_ptr),
                                                           byref(name_len),
                                                           byref(item))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            items[name] = component_item_from_ptr(item)
        return items

    def exports(self, engine: Engine) -> Dict[str, "ComponentItem"]:
        """
        Returns a dictionary of the exports of this component type.
        """
        n = ffi.wasmtime_component_type_export_count(self.ptr(), engine.ptr())
        items = {}
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            item = ffi.wasmtime_component_item_t()
            found = ffi.wasmtime_component_type_export_nth(self.ptr(),
                                                           engine.ptr(),
                                                           i,
                                                           byref(name_ptr),
                                                           byref(name_len),
                                                           byref(item))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            items[name] = component_item_from_ptr(item)
        return items


class ComponentInstanceType(Managed["ctypes._Pointer[ffi.wasmtime_component_instance_type_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ComponentInstanceType`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_instance_type_t]") -> None:
        ffi.wasmtime_component_instance_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_instance_type_t]") -> "ComponentInstanceType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_instance_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ComponentInstanceType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    def exports(self, engine: Engine) -> Dict[str, "ComponentItem"]:
        """
        Returns a dictionary of the exports of this component instance type.
        """
        n = ffi.wasmtime_component_instance_type_export_count(self.ptr(), engine.ptr())
        items = {}
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            item = ffi.wasmtime_component_item_t()
            found = ffi.wasmtime_component_instance_type_export_nth(self.ptr(),
                                                           engine.ptr(),
                                                           i,
                                                           byref(name_ptr),
                                                           byref(name_len),
                                                           byref(item))
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            items[name] = component_item_from_ptr(item)
            assert(found)
        return items


class ModuleType(Managed["ctypes._Pointer[ffi.wasmtime_module_type_t]"]):
    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `ModuleType`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_module_type_t]") -> None:
        ffi.wasmtime_module_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_module_type_t]") -> "ModuleType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_module_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ModuleType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    def imports(self, engine: Engine) -> List[ImportType]:
        """
        Returns a list of the imports of this module type.
        """
        n = ffi.wasmtime_module_type_import_count(self.ptr(), engine.ptr())
        items = []
        for i in range(n):
            item = ffi.wasmtime_module_type_import_nth(self.ptr(),
                                                       engine.ptr(),
                                                       i)
            items.append(ImportType._from_ptr(item))
        return items

    def exports(self, engine: Engine) -> List[ExportType]:
        """
        Returns a list of the exports of this module type.
        """
        n = ffi.wasmtime_module_type_export_count(self.ptr(), engine.ptr())
        items = []
        for i in range(n):
            item = ffi.wasmtime_module_type_export_nth(self.ptr(),
                                                       engine.ptr(),
                                                       i)
            items.append(ExportType._from_ptr(item))
        return items


class FuncType(Managed["ctypes._Pointer[ffi.wasmtime_component_func_type_t]"]):
    _owner: Any

    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `FuncType`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_func_type_t]") -> None:
        if self._owner is None:
            ffi.wasmtime_component_func_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_func_type_t]", owner: Any = None) -> "FuncType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_func_type_t)):
            raise TypeError("wrong pointer type")
        ty: "FuncType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty._owner = owner
        return ty

    @property
    def params(self) -> List[Tuple[str, 'ValType']]:
        """
        Returns the parameter types of this component function type.
        """
        n = ffi.wasmtime_component_func_type_param_count(self.ptr())
        items = []
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            valtype_ptr = ffi.wasmtime_component_valtype_t()
            found = ffi.wasmtime_component_func_type_param_nth(self.ptr(),
                                                               i,
                                                               byref(name_ptr),
                                                               byref(name_len),
                                                               byref(valtype_ptr))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            valtype = valtype_from_ptr(valtype_ptr)
            items.append((name, valtype))
        return items

    @property
    def result(self) -> Optional['ValType']:
        """
        Returns the result type of this component function type, if any.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        has_result = ffi.wasmtime_component_func_type_result(self.ptr(), byref(valtype_ptr))
        if not has_result:
            return None
        return valtype_from_ptr(valtype_ptr)


class ValType:
    @abstractmethod
    def add_classes(self, s: Set[type]) -> None:
        """
        Returns the python class that is created by `convert_from_c` and
        accepted by `convert_to_c`
        """
        pass

    @abstractmethod
    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        """
        Converts `val` to this type and stores it in `ptr`
        """
        pass

    @abstractmethod
    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        """
        Converts `val` to Python
        """
        pass


@dataclass
class Bool(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(bool)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, bool):
            raise TypeError("expected bool for Bool type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_BOOL
        ptr.contents.of.boolean = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_BOOL.value)
        return bool(c.of.boolean)


@dataclass
class S8(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for S8 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_S8
        ptr.contents.of.s8 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_S8.value)
        return int(c.of.s8)


@dataclass
class S16(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for S16 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_S16
        ptr.contents.of.s16 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_S16.value)
        return int(c.of.s16)


@dataclass
class S32(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for S32 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_S32
        ptr.contents.of.s32 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_S32.value)
        return int(c.of.s32)


@dataclass
class S64(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for S64 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_S64
        ptr.contents.of.s64 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_S64.value)
        return int(c.of.s64)


@dataclass
class U8(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for U8 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_U8
        ptr.contents.of.u8 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_U8.value)
        return int(c.of.u8)


@dataclass
class U16(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for U16 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_U16
        ptr.contents.of.u16 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_U16.value)
        return int(c.of.u16)


@dataclass
class U32(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for U32 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_U32
        ptr.contents.of.u32 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_U32.value)
        return int(c.of.u32)


@dataclass
class U64(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(int)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, int):
            raise TypeError("expected int for U64 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_U64
        ptr.contents.of.u64 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_U64.value)
        return int(c.of.u64)


@dataclass
class F32(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(float)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, float):
            raise TypeError("expected float for F32 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_F32
        ptr.contents.of.f32 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_F32.value)
        return float(c.of.f32)


@dataclass
class F64(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(float)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, float):
            raise TypeError("expected float for F64 type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_F64
        ptr.contents.of.f64 = val

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_F64.value)
        return float(c.of.f64)


@dataclass
class Char(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(str)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, str) or len(val) != 1:
            raise TypeError("expected single-character string for Char type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_CHAR
        ptr.contents.of.character = ord(val)

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_CHAR.value)
        return chr(c.of.character)



@dataclass
class String(ValType):
    def add_classes(self, s: Set[type]) -> None:
        s.add(str)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, str):
            raise TypeError("expected string type")
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_STRING
        ptr.contents.of.string = ffi.str_to_capi(val)

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_STRING.value)
        ret = ffi.to_str(c.of.string)
        ffi.wasm_byte_vec_delete(byref(c.of.string))
        return ret


@dataclass
class ErrorContext(ValType):
    def add_classes(self, s: Set[type]) -> None:
        raise NotImplementedError("ErrorContext conversion not implemented yet")

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        raise NotImplementedError("ErrorContext conversion not implemented yet")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        raise NotImplementedError("ErrorContext conversion not implemented yet")


class ListType(Managed["ctypes._Pointer[ffi.wasmtime_component_list_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_list_type_t]") -> None:
        ffi.wasmtime_component_list_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_list_type_t]") -> "ListType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_list_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ListType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def element(self) -> 'ValType':
        """
        Returns the element type of this list type.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        ffi.wasmtime_component_list_type_element(self.ptr(), byref(valtype_ptr))
        return valtype_from_ptr(valtype_ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ListType):
            return False
        return ffi.wasmtime_component_list_type_equal(self.ptr(), other.ptr())

    def _is_bytes(self) -> bool:
        return isinstance(self.element, U8)

    def add_classes(self, s: Set[type]) -> None:
        if self._is_bytes():
            s.add(bytes)
        else:
            s.add(list)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        element = self.element
        if self._is_bytes():
            if not isinstance(val, bytes):
                raise TypeError("expected bytes value")
        else:
            if not isinstance(val, list):
                raise TypeError("expected list value")
        assert(isinstance(val, (bytes, list))) # here for mypy
        raw = ffi.wasmtime_component_vallist_t()
        ffi.wasmtime_component_vallist_new_uninit(raw, len(val))
        i = 0
        cleanup = True
        try:
            for e in val:
                element.convert_to_c(store, e, ctypes.pointer(raw.data[i]))
                i += 1
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_LIST
            ptr.contents.of.list = raw
            cleanup = False
        finally:
            if not cleanup:
                return
            for j in range(i, len(val)):
                raw.data[j].kind = ffi.WASMTIME_COMPONENT_BOOL
                raw.data[j].of.boolean = False
            ffi.wasmtime_component_vallist_delete(byref(raw))


    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_LIST.value)
        try:
            ret = []
            element = self.element
            for i in range(c.of.record.size):
                raw_field = c.of.tuple.data[i]
                ret.append(element.convert_from_c(raw_field))
                raw_field.kind = ffi.WASMTIME_COMPONENT_BOOL
                raw_field.of.boolean = False
            if self._is_bytes():
                return bytes(ret)
            return ret
        finally:
            ffi.wasmtime_component_valtuple_delete(byref(c.of.tuple))


class RecordType(Managed["ctypes._Pointer[ffi.wasmtime_component_record_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_record_type_t]") -> None:
        ffi.wasmtime_component_record_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_record_type_t]") -> "RecordType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_record_type_t)):
            raise TypeError("wrong pointer type")
        ty: "RecordType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def fields(self) -> List[Tuple[str, 'ValType']]:
        """
        Returns the fields of this record type.
        """
        n = ffi.wasmtime_component_record_type_field_count(self.ptr())
        items = []
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            valtype_ptr = ffi.wasmtime_component_valtype_t()
            found = ffi.wasmtime_component_record_type_field_nth(self.ptr(),
                                                                 i,
                                                                 byref(name_ptr),
                                                                 byref(name_len),
                                                                 byref(valtype_ptr))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            valtype = valtype_from_ptr(valtype_ptr)
            items.append((name, valtype))
        return items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecordType):
            return False
        return ffi.wasmtime_component_record_type_equal(self.ptr(), other.ptr())

    def add_classes(self, s: Set[type]) -> None:
        s.add(Record)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        fields = self.fields
        raw = ffi.wasmtime_component_valrecord_t()
        ffi.wasmtime_component_valrecord_new_uninit(raw, len(fields))
        i = 0
        cleanup = True
        try:
            for name, ty in fields:
                ty.convert_to_c(store, getattr(val, name), ctypes.pointer(raw.data[i].val))
                raw.data[i].name = ffi.str_to_capi(name)
                i += 1
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_RECORD
            ptr.contents.of.record = raw
            cleanup = False
        finally:
            if not cleanup:
                return
            for j in range(i, len(fields)):
                raw.data[j].val.kind = ffi.WASMTIME_COMPONENT_BOOL
                raw.data[j].val.of.boolean = False
            ffi.wasmtime_component_valrecord_delete(byref(raw))


    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_RECORD.value)
        try:
            ret = Record()
            fields = self.fields
            for i, (name, ty) in zip(range(c.of.record.size), fields):
                raw_field = c.of.record.data[i]
                raw_name = ffi.to_str(raw_field.name)
                assert(raw_name == name)
                val = ty.convert_from_c(raw_field.val)
                setattr(ret, name, val)
                raw_field.val.kind = ffi.WASMTIME_COMPONENT_BOOL
                raw_field.val.of.boolean = False
            return ret
        finally:
            ffi.wasmtime_component_valrecord_delete(c.of.record)


class Record:
    def __eq__(self, other: Any) -> bool:
        for key, value in self.__dict__.items():
            if not hasattr(other, key) or getattr(other, key) != value:
                return False
        return True


class TupleType(Managed["ctypes._Pointer[ffi.wasmtime_component_tuple_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_tuple_type_t]") -> None:
        ffi.wasmtime_component_tuple_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_tuple_type_t]") -> "TupleType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_tuple_type_t)):
            raise TypeError("wrong pointer type")
        ty: "TupleType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def elements(self) -> List['ValType']:
        """
        Returns the element types of this tuple type.
        """
        n = ffi.wasmtime_component_tuple_type_types_count(self.ptr())
        items = []
        for i in range(n):
            valtype_ptr = ffi.wasmtime_component_valtype_t()
            found = ffi.wasmtime_component_tuple_type_types_nth(self.ptr(),
                                                                i,
                                                                byref(valtype_ptr))
            assert(found)
            valtype = valtype_from_ptr(valtype_ptr)
            items.append(valtype)
        return items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TupleType):
            return False
        return ffi.wasmtime_component_tuple_type_equal(self.ptr(), other.ptr())

    def add_classes(self, s: Set[type]) -> None:
        s.add(tuple)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        elements = self.elements
        if not isinstance(val, tuple):
            raise TypeError("expected tuple type")
        if len(val) != len(elements):
            raise TypeError("tuple length mismatch")
        raw = ffi.wasmtime_component_valtuple_t()
        ffi.wasmtime_component_valtuple_new_uninit(raw, len(elements))
        i = 0
        cleanup = True
        try:
            for ty, element in zip(elements, val):
                ty.convert_to_c(store, element, ctypes.pointer(raw.data[i]))
                i += 1
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_TUPLE
            ptr.contents.of.tuple = raw
            cleanup = False
        finally:
            if not cleanup:
                return
            for j in range(i, len(elements)):
                raw.data[j].kind = ffi.WASMTIME_COMPONENT_BOOL
                raw.data[j].of.boolean = False
            ffi.wasmtime_component_valtuple_delete(byref(raw))


    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_TUPLE.value)
        try:
            ret: List[Any] = []
            for i, ty in zip(range(c.of.record.size), self.elements):
                raw_field = c.of.tuple.data[i]
                ret.append(ty.convert_from_c(raw_field))
                raw_field.kind = ffi.WASMTIME_COMPONENT_BOOL
                raw_field.of.boolean = False
            return tuple(ret)
        finally:
            ffi.wasmtime_component_valtuple_delete(byref(c.of.tuple))


@dataclass
class Variant:
    tag: str
    payload: Optional[Any] = None


case_test_cache: Set[type] = set()


class VariantLikeType:
    @abstractmethod
    def _cases(self) -> List[Tuple[str, Optional['ValType']]]:
        pass

    def add_classes(self, s: Set[type]) -> None:
        if self._tagged():
            s.add(Variant)
        else:
            for _, ty in self._cases():
                if ty is None:
                    s.add(object)
                else:
                    ty.add_classes(s)

    def _tagged(self) -> bool:
        t: Set[type] = set()
        for _, ty in self._cases():
            case: Set[type] = set()
            if ty is None:
                case.add(object)
            else:
                ty.add_classes(case)
            if len(case & t) != 0:
                return True
            t |= case
        return False

    def _lower(self, store: Storelike, val: Any) -> Tuple[str, Optional['ctypes._Pointer[ffi.wasmtime_component_val_t]']]:
        tagged = self._tagged()
        if tagged and not isinstance(val, Variant):
            raise TypeError("expected Variant type")
        for name, ty in self._cases():
            if tagged:
                if name != val.tag:
                    continue
            elif ty is None:
                if val is not None:
                    continue
            else:
                case_test_cache.clear()
                ty.add_classes(case_test_cache)
                if not isinstance(val, tuple(case_test_cache)):
                    continue

            if ty is None:
                return (name, None)
            raw = ffi.wasmtime_component_val_t()
            if tagged:
                payload = val.payload
            else:
                payload = val
            ty.convert_to_c(store, payload, ctypes.pointer(raw))
            return (name, ffi.wasmtime_component_val_new(byref(raw)))
        raise ValueError('value not valid for this variant')

    def _lift(self, tag: str, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> Any:
        tagged = self._tagged()
        for name, ty in self._cases():
            if name != tag:
                continue
            if ty is None:
                if tagged:
                    return Variant(tag)
                return None
            payload = ty.convert_from_c(ptr.contents)
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_BOOL
            ptr.contents.of.boolean = False
            ffi.wasmtime_component_val_delete(ptr)
            if tagged:
                return Variant(tag, payload)
            return payload
        raise ValueError(f"tag {tag} not found in variant cases")


class VariantType(Managed["ctypes._Pointer[ffi.wasmtime_component_variant_type_t]"], ValType, VariantLikeType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_variant_type_t]") -> None:
        ffi.wasmtime_component_variant_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_variant_type_t]") -> "VariantType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_variant_type_t)):
            raise TypeError("wrong pointer type")
        ty: "VariantType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def cases(self) -> List[Tuple[str, Optional['ValType']]]:
        """
        Returns the cases of this variant type.
        """
        n = ffi.wasmtime_component_variant_type_case_count(self.ptr())
        items = []
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            has_payload = ctypes.c_bool()
            valtype_ptr = ffi.wasmtime_component_valtype_t()
            found = ffi.wasmtime_component_variant_type_case_nth(self.ptr(),
                                                                 i,
                                                                 byref(name_ptr),
                                                                 byref(name_len),
                                                                 byref(has_payload),
                                                                 byref(valtype_ptr))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            if has_payload.value:
                valtype = valtype_from_ptr(valtype_ptr)
            else:
                valtype = None
            items.append((name, valtype))
        return items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariantType):
            return False
        return ffi.wasmtime_component_variant_type_equal(self.ptr(), other.ptr())

    def _cases(self) -> List[Tuple[str, Optional['ValType']]]:
        return self.cases

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        name, raw = self._lower(store, val)
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_VARIANT
        ptr.contents.of.variant.discriminant = ffi.str_to_capi(name)
        ptr.contents.of.variant.val = raw

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_VARIANT.value)
        tag = ffi.to_str(c.of.variant.discriminant)
        ffi.wasm_byte_vec_delete(byref(c.of.variant.discriminant))
        return self._lift(tag, c.of.variant.val)


class EnumType(Managed["ctypes._Pointer[ffi.wasmtime_component_enum_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_enum_type_t]") -> None:
        ffi.wasmtime_component_enum_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_enum_type_t]") -> "EnumType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_enum_type_t)):
            raise TypeError("wrong pointer type")
        ty: "EnumType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def names_count(self) -> int:
        """
        Returns the numter of names of this enum type.
        """
        return ffi.wasmtime_component_enum_type_names_count(self.ptr())

    def name(self, n: int) -> Optional[str]:
        """
        Returns the nth name of this enum type.
        """
        name_ptr = ctypes.POINTER(ctypes.c_char)()
        name_len = ctypes.c_size_t()
        found = ffi.wasmtime_component_enum_type_names_nth(self.ptr(),
                                                           n,
                                                           byref(name_ptr),
                                                           byref(name_len))
        if found:
            return ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
        return None

    @property
    def names(self) -> List[str]:
        """
        Returns the names of this enum type.
        """
        items = []
        for i in range(self.names_count):
            name = self.name(i)
            assert(name is not None)
            items.append(name)
        return items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnumType):
            return False
        return ffi.wasmtime_component_enum_type_equal(self.ptr(), other.ptr())

    def add_classes(self, s: Set[type]) -> None:
        s.add(str)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if isinstance(val, str):
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_ENUM
            ptr.contents.of.enumeration = ffi.str_to_capi(val)
        else:
            raise TypeError("expected str type")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_ENUM.value)
        ret = ffi.to_str(c.of.enumeration)
        ffi.wasm_byte_vec_delete(byref(c.of.enumeration))
        return ret


class OptionType(Managed["ctypes._Pointer[ffi.wasmtime_component_option_type_t]"], ValType, VariantLikeType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_option_type_t]") -> None:
        ffi.wasmtime_component_option_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_option_type_t]") -> "OptionType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_option_type_t)):
            raise TypeError("wrong pointer type")
        ty: "OptionType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def payload(self) -> 'ValType':
        """
        Returns the payload type of this option type.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        ffi.wasmtime_component_option_type_ty(self.ptr(), byref(valtype_ptr))
        return valtype_from_ptr(valtype_ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OptionType):
            return False
        return ffi.wasmtime_component_option_type_equal(self.ptr(), other.ptr())

    def _cases(self) -> List[Tuple[str, Optional['ValType']]]:
        return [('none', None), ('some', self.payload)]

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        _, raw = self._lower(store, val)
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_OPTION
        ptr.contents.of.option = raw

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_OPTION.value)
        if c.of.option:
            tag = 'some'
        else:
            tag = 'none'
        return self._lift(tag, c.of.option)



class ResultType(Managed["ctypes._Pointer[ffi.wasmtime_component_result_type_t]"], ValType, VariantLikeType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_result_type_t]") -> None:
        ffi.wasmtime_component_result_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_result_type_t]") -> "ResultType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_result_type_t)):
            raise TypeError("wrong pointer type")
        ty: "ResultType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def ok(self) -> Optional['ValType']:
        """
        Returns the ok type of this result type, if any.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        has_ok = ffi.wasmtime_component_result_type_ok(self.ptr(), byref(valtype_ptr))
        if not has_ok:
            return None
        return valtype_from_ptr(valtype_ptr)

    @property
    def err(self) -> Optional['ValType']:
        """
        Returns the err type of this result type, if any.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        has_err = ffi.wasmtime_component_result_type_err(self.ptr(), byref(valtype_ptr))
        if not has_err:
            return None
        return valtype_from_ptr(valtype_ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResultType):
            return False
        return ffi.wasmtime_component_result_type_equal(self.ptr(), other.ptr())

    def _cases(self) -> List[Tuple[str, Optional['ValType']]]:
        return [('ok', self.ok), ('err', self.err)]

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        name, raw = self._lower(store, val)
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_RESULT
        ptr.contents.of.result.is_ok = name == 'ok'
        ptr.contents.of.result.val = raw

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_RESULT.value)
        if c.of.result.is_ok:
            tag = 'ok'
        else:
            tag = 'err'
        return self._lift(tag, c.of.result.val)


class FlagsType(Managed["ctypes._Pointer[ffi.wasmtime_component_flags_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_flags_type_t]") -> None:
        ffi.wasmtime_component_flags_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_flags_type_t]") -> "FlagsType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_flags_type_t)):
            raise TypeError("wrong pointer type")
        ty: "FlagsType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def names(self) -> List[str]:
        """
        Returns the names of this flags type.
        """
        n = ffi.wasmtime_component_flags_type_names_count(self.ptr())
        items = []
        for i in range(n):
            name_ptr = ctypes.POINTER(ctypes.c_char)()
            name_len = ctypes.c_size_t()
            found = ffi.wasmtime_component_flags_type_names_nth(self.ptr(),
                                                                i,
                                                                byref(name_ptr),
                                                                byref(name_len))
            assert(found)
            name = ctypes.string_at(name_ptr, name_len.value).decode('utf-8')
            items.append(name)
        return items

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlagsType):
            return False
        return ffi.wasmtime_component_flags_type_equal(self.ptr(), other.ptr())

    def add_classes(self, s: Set[type]) -> None:
        s.add(set)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if not isinstance(val, set):
            raise TypeError("expected set type for Flags type")
        for s in val:
            if not isinstance(s, str):
                raise TypeError("expected set of strings for Flags type")

        raw = ffi.wasmtime_component_valflags_t()
        ffi.wasmtime_component_valflags_new_uninit(raw, len(val))
        for i, s in enumerate(val):
            raw.data[i] = ffi.str_to_capi(s)
        ptr.contents.kind = ffi.WASMTIME_COMPONENT_FLAGS
        ptr.contents.of.flags = raw

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_FLAGS.value)
        result = set()
        for i in range(c.of.flags.size):
            s = ffi.to_str(c.of.flags.data[i])
            result.add(s)
        ffi.wasmtime_component_valflags_delete(byref(c.of.flags))
        return result


class FutureType(Managed["ctypes._Pointer[ffi.wasmtime_component_future_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_future_type_t]") -> None:
        ffi.wasmtime_component_future_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_future_type_t]") -> "FutureType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_future_type_t)):
            raise TypeError("wrong pointer type")
        ty: "FutureType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def payload(self) -> 'ValType':
        """
        Returns the payload type of this future type.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        ffi.wasmtime_component_future_type_ty(self.ptr(), byref(valtype_ptr))
        return valtype_from_ptr(valtype_ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FutureType):
            return False
        return ffi.wasmtime_component_future_type_equal(self.ptr(), other.ptr())

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        raise NotImplementedError("Future conversion not implemented yet")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        raise NotImplementedError("conversion not implemented yet")


class StreamType(Managed["ctypes._Pointer[ffi.wasmtime_component_stream_type_t]"], ValType):
    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_stream_type_t]") -> None:
        ffi.wasmtime_component_stream_type_delete(ptr)

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_stream_type_t]") -> "StreamType":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_stream_type_t)):
            raise TypeError("wrong pointer type")
        ty: "StreamType" = cls.__new__(cls)
        ty._set_ptr(ptr)
        return ty

    @property
    def payload(self) -> 'ValType':
        """
        Returns the payload type of this stream type.
        """
        valtype_ptr = ffi.wasmtime_component_valtype_t()
        ffi.wasmtime_component_stream_type_ty(self.ptr(), byref(valtype_ptr))
        return valtype_from_ptr(valtype_ptr)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StreamType):
            return False
        return ffi.wasmtime_component_stream_type_equal(self.ptr(), other.ptr())

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        raise NotImplementedError("Stream conversion not implemented yet")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        raise NotImplementedError("conversion not implemented yet")


@dataclass
class OwnType(ValType):
    ty: ResourceType

    def add_classes(self, s: Set[type]) -> None:
        s.add(ResourceAny)
        s.add(ResourceHost)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if isinstance(val, ResourceAny):
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_RESOURCE
            ptr.contents.of.resource = val._consume()
        elif isinstance(val, ResourceHost):
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_RESOURCE
            ptr.contents.of.resource = val.to_any(store)._consume()
        else:
            raise TypeError("expected ResourceAny or ResourceHost for Own type")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_RESOURCE.value)
        return ResourceAny._from_ptr(ffi.take_pointer(c.of, 'resource'))


@dataclass
class BorrowType(ValType):
    ty: ResourceType

    def add_classes(self, s: Set[type]) -> None:
        s.add(ResourceAny)
        s.add(ResourceHost)

    def convert_to_c(self, store: Storelike, val: Any, ptr: 'ctypes._Pointer[ffi.wasmtime_component_val_t]') -> None:
        if isinstance(val, ResourceAny):
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_RESOURCE
            ptr.contents.of.resource = ffi.wasmtime_component_resource_any_clone(val.ptr())
        elif isinstance(val, ResourceHost):
            ptr.contents.kind = ffi.WASMTIME_COMPONENT_RESOURCE
            ptr.contents.of.resource = val.to_any(store)._consume()
        else:
            raise TypeError("expected ResourceAny or ResourceHost for Own type")

    def convert_from_c(self, c: 'ffi.wasmtime_component_val_t') -> Any:
        assert(c.kind == ffi.WASMTIME_COMPONENT_RESOURCE.value)
        return ResourceAny._from_ptr(ffi.take_pointer(c.of, 'resource'))


ComponentItem = Union[
    ComponentType,
    ModuleType,
    ComponentInstanceType,
    ResourceType,
    ValType,
    FuncType,
]


def component_item_from_ptr(ptr: ffi.wasmtime_component_item_t) -> ComponentItem:
    if ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_COMPONENT.value:
        return ComponentType._from_ptr(ptr.of.component)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_MODULE.value:
        return ModuleType._from_ptr(ptr.of.module)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_COMPONENT_INSTANCE.value:
        return ComponentInstanceType._from_ptr(ptr.of.component_instance)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_RESOURCE.value:
        return ResourceType._from_ptr(ptr.of.resource)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_COMPONENT_FUNC.value:
        return FuncType._from_ptr(ptr.of.component_func)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_ITEM_TYPE.value:
        return valtype_from_ptr(ptr.of.type)
    else:
        ffi.wasmtime_component_item_delete(byref(ptr))
        raise TypeError("unknown component item kind")


def valtype_from_ptr(ptr: ffi.wasmtime_component_valtype_t) -> ValType:
    if ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_BOOL.value:
        return Bool()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_S8.value:
        return S8()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_S16.value:
        return S16()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_S32.value:
        return S32()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_S64.value:
        return S64()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_U8.value:
        return U8()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_U16.value:
        return U16()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_U32.value:
        return U32()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_U64.value:
        return U64()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_F32.value:
        return F32()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_F64.value:
        return F64()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_CHAR.value:
        return Char()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_STRING.value:
        return String()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_ERROR_CONTEXT.value:
        return ErrorContext()
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_LIST.value:
        return ListType._from_ptr(ptr.of.list)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_RECORD.value:
        return RecordType._from_ptr(ptr.of.record)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_TUPLE.value:
        return TupleType._from_ptr(ptr.of.tuple)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_VARIANT.value:
        return VariantType._from_ptr(ptr.of.variant)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_ENUM.value:
        return EnumType._from_ptr(ptr.of.enum_)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_OPTION.value:
        return OptionType._from_ptr(ptr.of.option)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_RESULT.value:
        return ResultType._from_ptr(ptr.of.result)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_FLAGS.value:
        return FlagsType._from_ptr(ptr.of.flags)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_FUTURE.value:
        return FutureType._from_ptr(ptr.of.future)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_STREAM.value:
        return StreamType._from_ptr(ptr.of.stream)
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_OWN.value:
        return OwnType(ResourceType._from_ptr(ptr.of.own))
    elif ptr.kind == ffi.WASMTIME_COMPONENT_VALTYPE_BORROW.value:
        return BorrowType(ResourceType._from_ptr(ptr.of.borrow))
    else:
        ffi.wasmtime_component_valtype_delete(byref(ptr))
        raise TypeError("unknown component value type kind")
