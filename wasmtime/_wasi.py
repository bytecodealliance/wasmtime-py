from ctypes import *
from wasmtime import Store, Trap, ImportType, WasmtimeError
from . import _ffi as ffi
from ._extern import wrap_extern
from ._config import setter_property
from typing import Optional, List, Iterable
from ._exportable import AsExtern


class WasiConfig:
    def __init__(self) -> None:
        self.__ptr__ = ffi.wasi_config_new()

    @setter_property
    def argv(self, argv: List[str]) -> None:
        """
        Explicitly configure the `argv` for this WASI configuration
        """
        ptrs = to_char_array(argv)
        ffi.wasi_config_set_argv(self.__ptr__, c_int(len(argv)), ptrs)

    def inherit_argv(self) -> None:
        ffi.wasi_config_inherit_argv(self.__ptr__)

    @setter_property
    def env(self, pairs: Iterable[Iterable]) -> None:
        """
        Configure environment variables to be returned for this WASI
        configuration.

        The `pairs` provided must be an iterable list of key/value pairs of
        environment variables.
        """
        names = []
        values = []
        for name, value in pairs:
            names.append(name)
            values.append(value)
        name_ptrs = to_char_array(names)
        value_ptrs = to_char_array(values)
        ffi.wasi_config_set_env(self.__ptr__, c_int(
            len(names)), name_ptrs, value_ptrs)

    def inherit_env(self) -> None:
        ffi.wasi_config_inherit_env(self.__ptr__)

    @setter_property
    def stdin_file(self, path: str) -> None:
        ffi.wasi_config_set_stdin_file(
            self.__ptr__, c_char_p(path.encode('utf-8')))

    def inherit_stdin(self) -> None:
        ffi.wasi_config_inherit_stdin(self.__ptr__)

    @setter_property
    def stdout_file(self, path: str) -> None:
        ffi.wasi_config_set_stdout_file(
            self.__ptr__, c_char_p(path.encode('utf-8')))

    def inherit_stdout(self) -> None:
        ffi.wasi_config_inherit_stdout(self.__ptr__)

    @setter_property
    def stderr_file(self, path: str) -> None:
        ffi.wasi_config_set_stderr_file(
            self.__ptr__, c_char_p(path.encode('utf-8')))

    def inherit_stderr(self) -> None:
        ffi.wasi_config_inherit_stderr(self.__ptr__)

    def preopen_dir(self, path: str, guest_path: str) -> None:
        path_ptr = c_char_p(path.encode('utf-8'))
        guest_path_ptr = c_char_p(guest_path.encode('utf-8'))
        ffi.wasi_config_preopen_dir(self.__ptr__, path_ptr, guest_path_ptr)

    def __del__(self) -> None:
        if hasattr(self, '__ptr__'):
            ffi.wasi_config_delete(self.__ptr__)


def to_char_array(strings: List[str]) -> "pointer[pointer[c_char]]":
    ptrs = (c_char_p * len(strings))()
    for i, s in enumerate(strings):
        ptrs[i] = c_char_p(s.encode('utf-8'))
    return cast(ptrs, POINTER(POINTER(c_char)))


class WasiInstance:
    __ptr__: "pointer[ffi.wasi_instance_t]"

    def __init__(self, store: Store, name: str, config: WasiConfig):
        if not isinstance(store, Store):
            raise TypeError("expected a `Store`")
        if not isinstance(name, str):
            raise TypeError("expected a `str`")
        name_bytes = name.encode('utf-8')
        if not isinstance(config, WasiConfig):
            raise TypeError("expected a `WasiConfig`")
        ptr = config.__ptr__
        delattr(config, '__ptr__')

        trap = POINTER(ffi.wasm_trap_t)()
        ptr = ffi.wasi_instance_new(
            store.__ptr__, c_char_p(name_bytes), ptr, byref(trap))
        if not ptr:
            if trap:
                raise Trap.__from_ptr__(trap)
            raise WasmtimeError("failed to create wasi instance")
        self.__ptr__ = ptr
        self.store = store

    def bind(self, import_: ImportType) -> Optional[AsExtern]:
        if not isinstance(import_, ImportType):
            raise TypeError("expected an `ImportType`")
        ptr = ffi.wasi_instance_bind_import(self.__ptr__, import_.__ptr__)
        if ptr:
            return wrap_extern(ptr, self)
        else:
            return None

    def __del__(self) -> None:
        if hasattr(self, '__ptr__'):
            ffi.wasi_instance_delete(self.__ptr__)
