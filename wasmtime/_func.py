from ctypes import POINTER, pointer, byref, CFUNCTYPE, c_void_p, cast
from wasmtime import Store, FuncType, Val, IntoVal, Trap, WasmtimeError
import sys
import traceback
from . import _ffi as ffi
from ._extern import wrap_extern
from typing import Callable, Optional, Generic, TypeVar, List, Union, Tuple, cast as cast_type, Any, Sequence
from ._exportable import AsExtern


class Func:
    _ptr: "pointer[ffi.wasm_func_t]"

    def __init__(self, store: Store, ty: FuncType, func: Callable, access_caller: bool = False):
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
        idx = FUNCTIONS.allocate((func, ty.results, store))
        if access_caller:
            ptr = ffi.wasmtime_func_new_with_env(
                store._ptr,
                ty._ptr,
                trampoline_with_caller,
                idx,
                finalize)
        else:
            ptr = ffi.wasm_func_new_with_env(
                store._ptr, ty._ptr, trampoline, idx, finalize)
        if not ptr:
            FUNCTIONS.deallocate(idx)
            raise WasmtimeError("failed to create func")
        self._ptr = ptr
        self._owner = None

    @classmethod
    def _from_ptr(cls, ptr: "pointer[ffi.wasm_func_t]", owner: Optional[Any]) -> "Func":
        ty: "Func" = cls.__new__(cls)
        if not isinstance(ptr, POINTER(ffi.wasm_func_t)):
            raise TypeError("wrong pointer type")
        ty._ptr = ptr
        ty._owner = owner
        return ty

    @property
    def type(self) -> FuncType:
        """
        Gets the type of this func as a `FuncType`
        """
        ptr = ffi.wasm_func_type(self._ptr)
        return FuncType._from_ptr(ptr, None)

    @property
    def param_arity(self) -> int:
        """
        Returns the number of parameters this function expects
        """
        return ffi.wasm_func_param_arity(self._ptr)

    @property
    def result_arity(self) -> int:
        """
        Returns the number of results this function produces
        """
        return ffi.wasm_func_result_arity(self._ptr)

    def __call__(self, *params: IntoVal) -> Union[IntoVal, Sequence[IntoVal], None]:
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

        ty = self.type
        param_tys = ty.params
        if len(params) > len(param_tys):
            raise WasmtimeError("too many parameters provided: given %s, expected %s" %
                                (len(params), len(param_tys)))
        if len(params) < len(param_tys):
            raise WasmtimeError("too few parameters provided: given %s, expected %s" %
                                (len(params), len(param_tys)))

        param_vals = [Val._convert(ty, params[i]) for i, ty in enumerate(param_tys)]
        params_ptr = (ffi.wasm_val_t * len(params))()
        for i, val in enumerate(param_vals):
            params_ptr[i] = val._unwrap_raw()
        params_arg = ffi.wasm_val_vec_t(len(params), params_ptr)

        result_tys = ty.results
        results_ptr = (ffi.wasm_val_t * len(result_tys))()
        results_arg = ffi.wasm_val_vec_t(len(result_tys), results_ptr)

        trap = POINTER(ffi.wasm_trap_t)()
        error = ffi.wasmtime_func_call(
            self._ptr,
            byref(params_arg),
            byref(results_arg),
            byref(trap))
        if error:
            raise WasmtimeError._from_ptr(error)
        if trap:
            raise Trap._from_ptr(trap)

        results = []
        for i in range(0, len(result_tys)):
            results.append(Val(results_ptr[i]).value)
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            return results

    def _as_extern(self) -> "pointer[ffi.wasm_extern_t]":
        return ffi.wasm_func_as_extern(self._ptr)

    def __del__(self) -> None:
        if hasattr(self, '_owner') and self._owner is None:
            ffi.wasm_func_delete(self._ptr)


class Caller:
    def __init__(self, ptr: pointer):
        self._ptr = ptr

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
        name_raw = ffi.str_to_name(name)

        # Next see if we've been invalidated
        if not hasattr(self, '_ptr'):
            return None

        # And if we're not invalidated we can perform the actual lookup
        ptr = ffi.wasmtime_caller_export_get(self._ptr, byref(name_raw))
        if ptr:
            return wrap_extern(ptr, None)
        else:
            return None


def extract_val(val: Val) -> IntoVal:
    a = val.value
    if a is not None:
        return a
    return val


@ffi.wasm_func_callback_with_env_t  # type: ignore
def trampoline(idx, params, results):  # type: ignore
    return invoke(idx, params.contents, results.contents, [])


@ffi.wasmtime_func_callback_with_env_t  # type: ignore
def trampoline_with_caller(caller, idx, params, results):  # type: ignore
    caller = Caller(caller)
    try:
        return invoke(idx, params.contents, results.contents, [caller])
    finally:
        delattr(caller, '_ptr')


def invoke(idx, params, results, pyparams):  # type: ignore
    func, result_tys, store = FUNCTIONS.get(idx or 0)

    try:
        for i in range(0, params.size):
            pyparams.append(Val._value(params.data[i]))
        pyresults = func(*pyparams)
        if results.size == 0:
            if pyresults is not None:
                raise WasmtimeError(
                    "callback produced results when it shouldn't")
        elif results.size == 1:
            if isinstance(pyresults, Val):
                # Because we are taking the inner value with `_into_raw`, we
                # need to ensure that we have a unique `Val`.
                val = pyresults._clone()
            else:
                val = Val._convert(result_tys[0], pyresults)
            results.data[0] = val._into_raw()
        else:
            if len(pyresults) != results.size:
                raise WasmtimeError("callback produced wrong number of results")
            for i, result in enumerate(pyresults):
                # Because we are taking the inner value with `_into_raw`, we
                # need to ensure that we have a unique `Val`.
                if isinstance(result, Val):
                    val = result._clone()
                else:
                    val = Val._convert(result_tys[i], result)
                results.data[i] = val._into_raw()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        fmt = traceback.format_exception(exc_type, exc_value, exc_traceback)
        trap = Trap(store, "\n".join(fmt))
        ptr = trap._ptr
        delattr(trap, '_ptr')
        return cast(ptr, c_void_p).value

    return 0


@CFUNCTYPE(None, c_void_p)
def finalize(idx):  # type: ignore
    FUNCTIONS.deallocate(idx or 0)


T = TypeVar('T')


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


FUNCTIONS: Slab[Tuple] = Slab()
