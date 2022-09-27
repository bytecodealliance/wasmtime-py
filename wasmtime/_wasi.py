from ctypes import *
import ctypes
from wasmtime import WasmtimeError
from . import _ffi as ffi
from ._config import setter_property
from typing import List, Iterable


class WasiConfig:
    def __init__(self) -> None:
        self._ptr = ffi.wasi_config_new()

    @setter_property
    def argv(self, argv: List[str]) -> None:
        """
        Explicitly configure the `argv` for this WASI configuration
        """
        ptrs = to_char_array(argv)
        ffi.wasi_config_set_argv(self._ptr, c_int(len(argv)), ptrs)

    def inherit_argv(self) -> None:
        ffi.wasi_config_inherit_argv(self._ptr)

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
        ffi.wasi_config_set_env(self._ptr, c_int(
            len(names)), name_ptrs, value_ptrs)

    def inherit_env(self) -> None:
        """
        Configures the environment variables available within WASI to be those
        in this own process's environment. All environment variables are
        inherited.
        """
        ffi.wasi_config_inherit_env(self._ptr)

    @setter_property
    def stdin_file(self, path: str) -> None:
        """
        Configures a file to be used as the stdin stream of this WASI
        configuration.

        Reads of the stdin stream will read the path specified.

        The file must already exist on the filesystem. If it cannot be
        opened then `WasmtimeError` is raised.
        """
        res = ffi.wasi_config_set_stdin_file(
            self._ptr, c_char_p(path.encode('utf-8')))
        if not res:
            raise WasmtimeError("failed to set stdin file")

    def inherit_stdin(self) -> None:
        """
        Configures this own process's stdin to be used as the WASI program's
        stdin.

        Reads of the stdin stream will read this process's stdin.
        """
        ffi.wasi_config_inherit_stdin(self._ptr)

    @setter_property
    def stdout_file(self, path: str) -> None:
        """
        Configures a file to be used as the stdout stream of this WASI
        configuration.

        Writes to stdout will be written to the file specified.

        The file specified will be created if it doesn't exist, or truncated if
        it already exists. It must be available to open for writing. If it
        cannot be opened for writing then `WasmtimeError` is raised.
        """
        res = ffi.wasi_config_set_stdout_file(
            self._ptr, c_char_p(path.encode('utf-8')))
        if not res:
            raise WasmtimeError("failed to set stdout file")

    def inherit_stdout(self) -> None:
        """
        Configures this own process's stdout to be used as the WASI program's
        stdout.

        Writes to stdout stream will write to this process's stdout.
        """
        ffi.wasi_config_inherit_stdout(self._ptr)

    @setter_property
    def stderr_file(self, path: str) -> None:
        """
        Configures a file to be used as the stderr stream of this WASI
        configuration.

        Writes to stderr will be written to the file specified.

        The file specified will be created if it doesn't exist, or truncated if
        it already exists. It must be available to open for writing. If it
        cannot be opened for writing then `WasmtimeError` is raised.
        """
        res = ffi.wasi_config_set_stderr_file(
            self._ptr, c_char_p(path.encode('utf-8')))
        if not res:
            raise WasmtimeError("failed to set stderr file")

    def inherit_stderr(self) -> None:
        """
        Configures this own process's stderr to be used as the WASI program's
        stderr.

        Writes to stderr stream will write to this process's stderr.
        """
        ffi.wasi_config_inherit_stderr(self._ptr)

    def preopen_dir(self, path: str, guest_path: str) -> None:
        path_ptr = c_char_p(path.encode('utf-8'))
        guest_path_ptr = c_char_p(guest_path.encode('utf-8'))
        ffi.wasi_config_preopen_dir(self._ptr, path_ptr, guest_path_ptr)

    def __del__(self) -> None:
        if hasattr(self, '_ptr'):
            ffi.wasi_config_delete(self._ptr)


def to_char_array(strings: List[str]) -> "ctypes._Pointer[ctypes._Pointer[c_char]]":
    ptrs = (c_char_p * len(strings))()
    for i, s in enumerate(strings):
        ptrs[i] = c_char_p(s.encode('utf-8'))
    return cast(ptrs, POINTER(POINTER(c_char)))
