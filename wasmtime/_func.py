from contextlib import contextmanager
from ctypes import POINTER, byref, CFUNCTYPE, c_void_p, cast
import ctypes
from wasmtime import Store, FuncType, Val, Trap, WasmtimeError
from . import _ffi as ffi
from ._extern import wrap_extern
from typing import Callable, Optional, Generic, TypeVar, List, Union, Tuple, cast as cast_type, Sequence, Any
from ._exportable import AsExtern
from ._store import Storelike


T = TypeVar('T')
FUNCTIONS: "Slab[Tuple]"
LAST_EXCEPTION: Optional[Exception] = None


class Func:
    _func: ffi.wasmtime_func_t

    def __init__(self, store: Storelike, ty: FuncType, func: Callable, access_caller: bool = False):
        """
        Creates a new func in `store` with the given `ty` which calls the closure
        given

        The `func` is called with the parameters natively and they'll have native
        Python values rather than being wrapped in `Val`. If `access_caller` is
        set to `True` then the first argument given to `func` is an instance of
        type `Caller` below.
        """

        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, FuncType):
            raise TypeError("expected a FuncType")
        idx = FUNCTIONS.allocate((func, ty.results, access_caller))
        _func = ffi.wasmtime_func_t()
        ffi.wasmtime_func_new(
            store._context(),
            ty.ptr(),
            trampoline,
            idx,
            finalize,
            byref(_func))
        self._func = _func

    @classmethod
    def _from_raw(cls, func: ffi.wasmtime_func_t) -> "Func":
        ty: "Func" = cls.__new__(cls)
        ty._func = func
        return ty

    def type(self, store: Storelike) -> FuncType:
        """
        Gets the type of this func as a `FuncType`
        """
        ptr = ffi.wasmtime_func_type(store._context(), byref(self._func))
        return FuncType._from_ptr(ptr, None)

    def __call__(self, store: Storelike, *params: Any) -> Any:
        """
        Calls this function with the given parameters

        Parameters can either be a `Val` or a native python value which can be
        converted to a `Val` of the corresponding correct type

        Returns `None` if this func has 0 return types
        Returns a single value if the func has 1 return type
        Returns a list if the func has more than 1 return type

        Note that you can also use the `__call__` method and invoke a `Func` as
        if it were a function directly.
        """

        ty = self.type(store)
        param_tys = ty.params
        if len(params) > len(param_tys):
            raise WasmtimeError("too many parameters provided: given %s, expected %s" %
                                (len(params), len(param_tys)))
        if len(params) < len(param_tys):
            raise WasmtimeError("too few parameters provided: given %s, expected %s" %
                                (len(params), len(param_tys)))

        params_ptr = (ffi.wasmtime_val_t * len(params))()
        params_set = 0
        try:
            for val in params:
                params_ptr[params_set] = Val._convert_to_raw(store, param_tys[params_set], val)
                params_set += 1

            result_tys = ty.results
            results_ptr = (ffi.wasmtime_val_t * len(result_tys))()

            with enter_wasm(store) as trap:
                error = ffi.wasmtime_func_call(
                    store._context(),
                    byref(self._func),
                    params_ptr,
                    len(params),
                    results_ptr,
                    len(result_tys),
                    trap)
                if error:
                    raise WasmtimeError._from_ptr(error)
        finally:
            for i in range(0, params_set):
                ffi.wasmtime_val_unroot(store._context(), byref(params_ptr[i]))

        results = []
        for i in range(0, len(result_tys)):
            results.append(Val._from_raw(store, results_ptr[i]).value)
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            return results

    def _as_extern(self) -> ffi.wasmtime_extern_t:
        union = ffi.wasmtime_extern_union(func=self._func)
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_FUNC, union)


class Caller:
    __ptr: "Optional[ctypes._Pointer[ffi.wasmtime_caller_t]]"
    __context: "Optional[ctypes._Pointer[ffi.wasmtime_context_t]]"

    def __init__(self, ptr: "ctypes._Pointer[ffi.wasmtime_caller_t]"):
        self.__ptr = ptr
        self.__context = ffi.wasmtime_caller_context(ptr)

    def __getitem__(self, name: str) -> AsExtern:
        """
        Looks up an export with `name` on the calling module.

        If `name` isn't defined on the calling module, or if the caller has gone
        away for some reason, then this will raise a `KeyError`. For more
        information about when this could fail see the `get` method which
        returns `None` on failure.
        """

        ret = self.get(name)
        if ret is None:
            raise KeyError("failed to find export {}".format(name))
        return ret

    def get(self, name: str) -> Optional[AsExtern]:
        """
        Looks up an export with `name` on the calling module.

        May return `None` if the export isn't found, if it's not a memory (for
        now), or if the caller has gone away and this `Caller` object has
        persisted too long.
        """

        # First convert to a raw name so we can typecheck our argument
        name_bytes = name.encode('utf-8')
        name_buf = ffi.create_string_buffer(name_bytes)

        # Next see if we've been invalidated
        if self.__ptr is None:
            return None

        # And if we're not invalidated we can perform the actual lookup
        item = ffi.wasmtime_extern_t()
        ok = ffi.wasmtime_caller_export_get(self.__ptr, name_buf, len(name_bytes), byref(item))
        if ok:
            return wrap_extern(item)
        else:
            return None

    def _context(self) -> "ctypes._Pointer[ffi.wasmtime_context_t]":
        if self.__context is None:
            raise ValueError("caller is no longer valid")
        return self.__context

    def _invalidate(self) -> None:
        self.__ptr = None
        self.__context = None


def extract_val(val: Val) -> Any:
    a = val.value
    if a is not None:
        return a
    return val


@ffi.wasmtime_func_callback_t  # type: ignore
def trampoline(idx, caller, params, nparams, results, nresults):
    caller = Caller(caller)
    try:
        func, result_tys, access_caller = FUNCTIONS.get(idx or 0)
        pyparams = []
        if access_caller:
            pyparams.append(caller)

        for i in range(0, nparams):
            pyparams.append(Val._from_raw(caller, params[i], owned=False).value)
        pyresults = func(*pyparams)
        if nresults == 0:
            if pyresults is not None:
                raise WasmtimeError(
                    "callback produced results when it shouldn't")
        elif nresults == 1:
            results[0] = Val._convert_to_raw(caller, result_tys[0], pyresults)
        else:
            if len(pyresults) != nresults:
                raise WasmtimeError("callback produced wrong number of results")
            for i, result in enumerate(pyresults):
                results[i] = Val._convert_to_raw(caller, result_tys[i], result)
        return 0
    except Exception as e:
        global LAST_EXCEPTION
        LAST_EXCEPTION = e
        trap = Trap("python exception")._consume()
        return cast(trap, c_void_p).value
    finally:
        caller._invalidate()


@CFUNCTYPE(None, c_void_p)
def finalize(idx):  # type: ignore
    FUNCTIONS.deallocate(idx or 0)


class Slab(Generic[T]):
    list: List[Union[int, T]]
    next: int

    def __init__(self) -> None:
        self.list = []
        self.next = 0

    def allocate(self, val: T) -> int:
        idx = self.next

        if len(self.list) == idx:
            self.list.append(0)
            self.next += 1
        else:
            self.next = cast_type(int, self.list[idx])

        self.list[idx] = val
        return idx

    def get(self, idx: int) -> T:
        return cast_type(T, self.list[idx])

    def deallocate(self, idx: int) -> None:
        self.list[idx] = self.next
        self.next = idx


FUNCTIONS = Slab()


@contextmanager
def enter_wasm(store: Storelike):  # type: ignore
    try:
        trap = POINTER(ffi.wasm_trap_t)()
        yield byref(trap)
        if trap:
            trap_obj = Trap._from_ptr(trap)
            maybe_raise_last_exn()
            raise trap_obj
    except WasmtimeError:
        maybe_raise_last_exn()
        raise


def maybe_raise_last_exn() -> None:
    global LAST_EXCEPTION
    if LAST_EXCEPTION is None:
        return
    exn = LAST_EXCEPTION
    LAST_EXCEPTION = None
    raise exn
