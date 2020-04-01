from ._ffi import *
from ctypes import *
from wasmtime import Store, FuncType, Val, Trap, Extern
import sys
import traceback

dll.wasm_func_new_with_env.restype = P_wasm_func_t
dll.wasmtime_func_new_with_env.restype = P_wasm_func_t
dll.wasm_func_type.restype = P_wasm_functype_t
dll.wasm_func_param_arity.restype = c_size_t
dll.wasm_func_result_arity.restype = c_size_t
dll.wasm_func_call.restype = P_wasm_trap_t
dll.wasm_func_as_extern.restype = P_wasm_extern_t
dll.wasmtime_caller_export_get.restype = P_wasm_extern_t


class Func(object):
    # Creates a new func in `store` with the given `ty` which calls the closure
    # given
    #
    # The `func` is called with the parameters natively and they'll have native
    # Python values rather than being wrapped in `Val`. If `access_caller` is
    # set to `True` then the first argument given to `func` is an instance of
    # type `Caller` below.
    def __init__(self, store, ty, func, access_caller=False):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, FuncType):
            raise TypeError("expected a FuncType")
        idx = FUNCTIONS.allocate((func, ty.params(), ty.results(), store))
        if access_caller:
            ptr = dll.wasmtime_func_new_with_env(
                store.__ptr__,
                ty.__ptr__,
                trampoline_with_caller,
                idx,
                finalize)
        else:
            ptr = dll.wasm_func_new_with_env(
                store.__ptr__, ty.__ptr__, trampoline, idx, finalize)
        if not ptr:
            FUNCTIONS.deallocate(idx)
            raise RuntimeError("failed to create func")
        self.__ptr__ = ptr
        self.__owner__ = None

    @classmethod
    def __from_ptr__(cls, ptr, owner):
        ty = cls.__new__(cls)
        if not isinstance(ptr, P_wasm_func_t):
            raise TypeError("wrong pointer type")
        ty.__ptr__ = ptr
        ty.__owner__ = owner
        return ty

    # Gets the type of this func as a `FuncType`
    def type(self):
        ptr = dll.wasm_func_type(self.__ptr__)
        return FuncType.__from_ptr__(ptr, None)

    # Returns the number of parameters this function expects
    def param_arity(self):
        return dll.wasm_func_param_arity(self.__ptr__)

    # Returns the number of results this function produces
    def result_arity(self):
        return dll.wasm_func_result_arity(self.__ptr__)

    # Calls this function with the given parameters
    #
    # Parameters can either be a `Val` or a native python value which can be
    # converted to a `Val` of the corresponding correct type
    #
    # Returns `None` if this func has 0 return types
    # Returns a single value if the func has 1 return type
    # Returns a list if the func has more than 1 return type
    def call(self, *params):
        return self(*params)

    def __call__(self, *params):
        ty = self.type()
        param_tys = ty.params()
        if len(param_tys) != len(params):
            raise TypeError("wrong number of parameters")
        param_ffi = (wasm_val_t * len(params))()
        for i, param in enumerate(params):
            val = Val.__convert__(param_tys[i], param)
            param_ffi[i] = val.__raw__

        result_tys = ty.results()
        result_ffi = (wasm_val_t * len(result_tys))()

        trap = dll.wasm_func_call(self.__ptr__, param_ffi, result_ffi)
        if trap:
            raise Trap.__from_ptr__(trap)

        results = []
        for i in range(0, len(result_tys)):
            results.append(extract_val(Val(result_ffi[i])))
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            return results

    # Returns this as an instance of `Extern`
    def as_extern(self):
        ptr = dll.wasm_func_as_extern(self.__ptr__)
        return Extern.__from_ptr__(ptr, self.__owner__ or self)

    def __del__(self):
        if hasattr(self, '__owner__') and self.__owner__ is None:
            dll.wasm_func_delete(self.__ptr__)


class Caller(object):
    def __init__(self, ptr):
        self.__ptr__ = ptr

    # Looks up an export with `name` on the calling module.
    #
    # May return `None` if the export isn't found, if it's not a memory (for
    # now), or if the caller has gone away and this `Caller` object has
    # persisted too long.
    def get_export(self, name):
        # First convert to a raw name so we can typecheck our argument
        name_raw = str_to_name(name)

        # Next see if we've been invalidated
        if not hasattr(self, '__ptr__'):
            return None

        # And if we're not invalidated we can perform the actual lookup
        ptr = dll.wasmtime_caller_export_get(self.__ptr__, byref(name_raw))
        if ptr:
            return Extern.__from_ptr__(ptr, None)
        else:
            return None


def extract_val(val):
    a = val.get()
    if a is not None:
        return a
    return val


@CFUNCTYPE(c_size_t, c_size_t, POINTER(wasm_val_t), POINTER(wasm_val_t))
def trampoline(idx, params_ptr, results_ptr):
    return invoke(idx, params_ptr, results_ptr, [])


@CFUNCTYPE(
    c_size_t,
    P_wasmtime_caller_t,
    c_size_t,
    POINTER(wasm_val_t),
    POINTER(wasm_val_t),
)
def trampoline_with_caller(caller, idx, params_ptr, results_ptr):
    caller = Caller(caller)
    try:
        return invoke(idx, params_ptr, results_ptr, [caller])
    finally:
        delattr(caller, '__ptr__')


def invoke(idx, params_ptr, results_ptr, params):
    func, param_tys, result_tys, store = FUNCTIONS.get(idx)

    try:
        for i in range(0, len(param_tys)):
            params.append(extract_val(Val(params_ptr[i])))
        results = func(*params)
        if len(result_tys) == 0:
            if results is not None:
                raise RuntimeError(
                    "callback produced results when it shouldn't")
        elif len(result_tys) == 1:
            val = Val.__convert__(result_tys[0], results)
            results_ptr[0] = val.__raw__
        else:
            if len(results) != len(result_tys):
                raise RuntimeError("callback produced wrong number of results")
            for i, result in enumerate(results):
                val = Val.__convert__(result_tys[i], result)
                results_ptr[i] = val.__raw__
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        fmt = traceback.format_exception(exc_type, exc_value, exc_traceback)
        trap = Trap(store, "\n".join(fmt))
        ptr = trap.__ptr__
        delattr(trap, '__ptr__')
        return cast(ptr, c_void_p).value

    return 0


@CFUNCTYPE(None, c_size_t)
def finalize(idx):
    FUNCTIONS.deallocate(idx)
    pass


class Slab(object):
    def __init__(self):
        self.list = []
        self.next = 0

    def allocate(self, val):
        idx = self.next

        if len(self.list) == idx:
            self.list.append(None)
            self.next += 1
        else:
            self.next = self.list[idx]

        self.list[idx] = val
        return idx

    def get(self, idx):
        return self.list[idx]

    def deallocate(self, idx):
        self.list[idx] = self.next
        self.next = idx


FUNCTIONS = Slab()
