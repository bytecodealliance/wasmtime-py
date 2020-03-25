from .ffi import *
from ctypes import *
from wasmtime import Store, FuncType, Val, Trap, Extern
import sys
import traceback

dll.wasm_func_new_with_env.restype = P_wasm_func_t
dll.wasm_func_type.restype = P_wasm_functype_t
dll.wasm_func_param_arity.restype = c_size_t
dll.wasm_func_result_arity.restype = c_size_t
dll.wasm_func_call.restype = P_wasm_trap_t
dll.wasm_func_as_extern.restype = P_wasm_extern_t


class Func:
    # Creates a new func in `store` with the given `ty` which calls the closure
    # given
    def __init__(self, store, ty, func):
        if not isinstance(store, Store):
            raise TypeError("expected a Store")
        if not isinstance(ty, FuncType):
            raise TypeError("expected a FuncType")
        idx = FUNCTIONS.allocate((func, ty.params(), ty.results(), store))
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
            trap = Trap.__from_ptr__(trap)
            raise RuntimeError(trap.message())

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


def extract_val(val):
    a = val.get()
    if a is not None:
        return a
    return val


@CFUNCTYPE(c_size_t, c_size_t, POINTER(wasm_val_t), POINTER(wasm_val_t))
def trampoline(idx, params_ptr, results_ptr):
    func, param_tys, result_tys, store = FUNCTIONS.get(idx)

    try:
        params = []
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


class Slab:
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
