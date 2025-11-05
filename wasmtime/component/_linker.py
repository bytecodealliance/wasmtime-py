import ctypes
from ctypes import POINTER, byref, create_string_buffer, CFUNCTYPE, c_void_p
from .. import Managed, Engine, WasmtimeError, Module, _ffi as ffi, Storelike, StoreContext
from .._config import setter_property
from ._instance import Instance
from ._component import Component
from ._resource_type import ResourceType
from typing import Union, Tuple, Callable, Optional, List, Any
from .._func import Slab
from ._enter import catch_exceptions
from ._types import ValType, FuncType

LinkerInstanceParent = Union['Linker', 'LinkerInstance']

ResourceDtor = Callable[[StoreContext, int], None]
RESOURCE_DTORS: Slab[ResourceDtor] = Slab()

UserFunc = Callable[..., Optional[Any]]
FUNCTIONS: Slab[UserFunc] = Slab()


class Linker(Managed["ctypes._Pointer[ffi.wasmtime_component_linker_t]"]):
    engine: Engine
    locked: bool

    def __init__(self, engine: Engine):
        """
        Creates a new linker ready to instantiate modules within the store
        provided.
        """
        self._set_ptr(ffi.wasmtime_component_linker_new(engine.ptr()))
        self.engine = engine
        self.locked = False

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_linker_t]") -> None:
        self._assert_not_locked()
        ffi.wasmtime_component_linker_delete(ptr)

    @setter_property
    def allow_shadowing(self, allow: bool) -> None:
        """
        Configures whether definitions are allowed to shadow one another within
        this linker
        """
        self._assert_not_locked()
        ffi.wasmtime_component_linker_allow_shadowing(self.ptr(), allow)

    def _assert_not_locked(self) -> None:
        if self.locked:
            raise WasmtimeError("cannot use linker while it's in use by other instances")

    def root(self) -> "LinkerInstance":
        """
        Returns the root instance used to defined new items in this linker.

        While this root instance is alive this linker cannot be used for any
        other operations. Until the returned object is destroyed this linker is
        considered "locked".

        It's recommended to bind the return value in a `with` block to
        automatically dispose of it when it's done.
        """
        self._assert_not_locked()
        ptr = ffi.wasmtime_component_linker_root(self.ptr())
        return LinkerInstance._from_ptr(ptr, self)

    def add_wasip2(self) -> None:
        """
        Adds the WASIp2 API definitions, from Wasmtime, in this linker.
        """
        self._assert_not_locked()
        err = ffi.wasmtime_component_linker_add_wasip2(self.ptr())
        if err:
            raise WasmtimeError._from_ptr(err)

    def instantiate(self, store: Storelike, component: Component) -> Instance:
        """
        Instantiates the given component using this linker within the provided
        store.

        Returns the instantiated `Instance` on success.
        """
        self._assert_not_locked()
        instance = ffi.wasmtime_component_instance_t()
        err = ffi.wasmtime_component_linker_instantiate(
            self.ptr(),
            store._context(),
            component.ptr(),
            byref(instance))
        if err:
            raise WasmtimeError._from_ptr(err)
        return Instance._from_raw(instance)

    def define_unknown_imports_as_traps(self, component: Component) -> None:
        """
        Configures this linker to define any unknown imports of `component` as
        traps which will error when invoked.
        """
        self._assert_not_locked()
        err = ffi.wasmtime_component_linker_define_unknown_imports_as_traps(
            self.ptr(),
            component.ptr())
        if err:
            raise WasmtimeError._from_ptr(err)


class LinkerInstance(Managed["ctypes._Pointer[ffi.wasmtime_component_linker_instance_t]"]):
    parent: Union[LinkerInstanceParent, None]
    locked: bool

    def __init__(self) -> None:
        raise WasmtimeError("Cannot directly construct a `LinkerInstance`")

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasmtime_component_linker_instance_t]") -> None:
        self._assert_not_locked()
        ffi.wasmtime_component_linker_instance_delete(ptr)
        assert(self.parent is not None)
        assert(self.parent.locked)
        self.parent.locked = False
        self.parent = None

    def _assert_not_locked(self) -> None:
        if self.locked:
            raise WasmtimeError("cannot use linker instance while it's in use by other instances")

    @classmethod
    def _from_ptr(cls, ptr: "ctypes._Pointer[ffi.wasmtime_component_linker_instance_t]", parent: LinkerInstanceParent) -> "LinkerInstance":
        if not isinstance(ptr, POINTER(ffi.wasmtime_component_linker_instance_t)):
            raise TypeError("wrong pointer type")
        ty: "LinkerInstance" = cls.__new__(cls)
        ty._set_ptr(ptr)
        ty.parent = parent
        ty.locked = False
        assert(not parent.locked)
        parent.locked = True
        return ty


    def add_instance(self, name: str) -> "LinkerInstance":
        """
        Adds a new instance to this linker instance under the given name.

        Returns a new `LinkerInstance` which can be used to define further
        items.

        While the returned instance is alive this linker instance cannot be
        used for other operations. Until the returned object is destroyed this
        linker instance is considered "locked".

        It's recommended to bind the return value in a `with` block to
        automatically dispose of it when it's done.
        """
        self._assert_not_locked()
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        ptr = POINTER(ffi.wasmtime_component_linker_instance_t)()
        err = ffi.wasmtime_component_linker_instance_add_instance(self.ptr(),
                                                                  name_buf,
                                                                  len(name_bytes),
                                                                  byref(ptr))
        if err:
            raise WasmtimeError._from_ptr(err)
        return LinkerInstance._from_ptr(ptr, self)

    def add_module(self, name: str, module: Module) -> None:
        """
        Adds a new module to this linker instance under the given name.
        """
        self._assert_not_locked()
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        err = ffi.wasmtime_component_linker_instance_add_module(self.ptr(),
                                                                name_buf,
                                                                len(name_bytes),
                                                                module.ptr())
        if err:
            raise WasmtimeError._from_ptr(err)

    def add_resource(self, name: str, ty: ResourceType, dtor: ResourceDtor) -> None:
        """
        Defines a the resource type `ty` under `name`

        When a value of this resource is destroyed then `dtor` is invoked.
        """
        self._assert_not_locked()
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        idx = RESOURCE_DTORS.allocate(dtor)
        err = ffi.wasmtime_component_linker_instance_add_resource(self.ptr(),
                                                                  name_buf,
                                                                  len(name_bytes),
                                                                  ty.ptr(),
                                                                  resource_dtor_impl,
                                                                  idx,
                                                                  resource_dtor_finalize)
        if err:
            raise WasmtimeError._from_ptr(err)

    def add_func(self, name: str, func: UserFunc) -> None:
        self._assert_not_locked()
        name_bytes = name.encode('utf-8')
        name_buf = create_string_buffer(name_bytes)
        idx = FUNCTIONS.allocate(func)
        err = ffi.wasmtime_component_linker_instance_add_func(self.ptr(),
                                                              name_buf,
                                                              len(name_bytes),
                                                              func_impl,
                                                              idx,
                                                              func_finalize)
        if err:
            raise WasmtimeError._from_ptr(err)


@ffi.wasmtime_component_resource_destructor_t
def resource_dtor_impl(idx, context, rep): # type: ignore
    def run(store: StoreContext) -> None:
        return RESOURCE_DTORS.get(idx or 0)(store, rep)
    return catch_exceptions(context, run)


@CFUNCTYPE(None, c_void_p)
def resource_dtor_finalize(idx): # type: ignore
    if RESOURCE_DTORS:
        RESOURCE_DTORS.deallocate(idx or 0)
    return None


@ffi.wasmtime_component_func_callback_t
def func_impl(idx, context, ty_raw, args, nargs, results, nresults): # type: ignore
    def run(store: StoreContext) -> None:
        with FuncType._from_ptr(ty_raw, owner=store) as fty:
            func = FUNCTIONS.get(idx or 0)
            param_tys = fty.params
            result_ty = fty.result
            assert(len(param_tys) == nargs)
            if result_ty is None:
                assert(nresults == 0)
            else:
                assert(nresults == 1)

            pyargs = []
            for (_, ty), i in zip(param_tys, range(nargs)):
                val = ty.convert_from_c(args[i])
                pyargs.append(val)
            result = func(store, *pyargs)

            if result_ty is None:
                assert(result is None)
            else:
                result_ty.convert_to_c(store, result, results)
    return catch_exceptions(context, run)


@CFUNCTYPE(None, c_void_p)
def func_finalize(idx): # type: ignore
    if FUNCTIONS:
        FUNCTIONS.deallocate(idx or 0)
    return None
