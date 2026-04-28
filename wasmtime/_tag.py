import ctypes
from . import _ffi as ffi
from wasmtime import WasmtimeError
from typing import TYPE_CHECKING
from ._store import Storelike
from ._types import TagType


class Tag:
    """
    Represents a WebAssembly tag, used to identify exception types.

    Tags are associated with a store and describe the payload signature
    of exceptions that can be thrown and caught.
    """

    _tag: ffi.wasmtime_tag_t

    def __init__(self, store: Storelike, ty: TagType) -> None:
        """
        Creates a new host-defined tag with the given tag type.

        Raises `WasmtimeError` if the tag cannot be created.
        """
        if not isinstance(ty, TagType):
            raise TypeError("expected a TagType")
        tag = ffi.wasmtime_tag_t()
        error = ffi.wasmtime_tag_new(store._context(), ty.ptr(), ctypes.byref(tag))
        if error:
            raise WasmtimeError._from_ptr(error)
        self._tag = tag

    @classmethod
    def _from_raw(cls, tag: ffi.wasmtime_tag_t) -> "Tag":
        obj = cls.__new__(cls)
        obj._tag = tag
        return obj

    def type(self, store: Storelike) -> TagType:
        """
        Returns the type of this tag.
        """
        ptr = ffi.wasmtime_tag_type(store._context(), ctypes.byref(self._tag))
        return TagType._from_ptr(ptr)

    def eq(self, store: Storelike, other: "Tag") -> bool:
        """
        Tests whether two tags are identical (same definition).
        """
        return bool(ffi.wasmtime_tag_eq(store._context(),
                                   ctypes.byref(self._tag),
                                   ctypes.byref(other._tag)))

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(tag=self._tag)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_TAG, union)
