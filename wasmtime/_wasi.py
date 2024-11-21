import ctypes
from ctypes import POINTER, c_char, c_char_p, cast
from enum import Enum
from os import PathLike
from typing import Iterable, List, Union

from wasmtime import Managed, WasmtimeError

from . import _ffi as ffi
from ._config import setter_property


def _encode_path(path: Union[str, bytes, PathLike]) -> bytes:
    if isinstance(path, (bytes, str)):
        path2 = path
    else:
        path2 = path.__fspath__()
    if isinstance(path2, bytes):
        return path2
    return path2.encode('utf8')

class DirPerms(Enum):
    READ_ONLY = ffi.wasi_dir_perms_flags.WASMTIME_WASI_DIR_PERMS_READ.value
    WRITE_ONLY = ffi.wasi_dir_perms_flags.WASMTIME_WASI_DIR_PERMS_WRITE.value
    READ_WRITE = ffi.wasi_dir_perms_flags.WASMTIME_WASI_DIR_PERMS_READ.value | ffi.wasi_dir_perms_flags.WASMTIME_WASI_DIR_PERMS_WRITE.value

class FilePerms(Enum):
    READ_ONLY = ffi.wasi_file_perms_flags.WASMTIME_WASI_FILE_PERMS_READ.value
    WRITE_ONLY = ffi.wasi_file_perms_flags.WASMTIME_WASI_FILE_PERMS_WRITE.value
    READ_WRITE = ffi.wasi_file_perms_flags.WASMTIME_WASI_FILE_PERMS_READ.value | ffi.wasi_file_perms_flags.WASMTIME_WASI_FILE_PERMS_WRITE.value

class WasiConfig(Managed["ctypes._Pointer[ffi.wasi_config_t]"]):

    def __init__(self) -> None:
        self._set_ptr(ffi.wasi_config_new())

    def _delete(self, ptr: "ctypes._Pointer[ffi.wasi_config_t]") -> None:
        ffi.wasi_config_delete(ptr)

    @setter_property
    def argv(self, argv: List[str]) -> None:
        """
        Explicitly configure the `argv` for this WASI configuration
        """
        ptrs = to_char_array(argv)
        if not ffi.wasi_config_set_argv(self.ptr(), len(argv), ptrs):
            raise WasmtimeError("failed to configure argv")

    def inherit_argv(self) -> None:
        ffi.wasi_config_inherit_argv(self.ptr())

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
        if not ffi.wasi_config_set_env(self.ptr(), len(names), name_ptrs, value_ptrs):
            raise WasmtimeError("failed to configure environment")

    def inherit_env(self) -> None:
        """
        Configures the environment variables available within WASI to be those
        in this own process's environment. All environment variables are
        inherited.
        """
        ffi.wasi_config_inherit_env(self.ptr())

    @setter_property
    def stdin_file(self, path: Union[str, bytes, PathLike]) -> None:
        """
        Configures a file to be used as the stdin stream of this WASI
        configuration.

        Reads of the stdin stream will read the path specified.

        The file must already exist on the filesystem. If it cannot be
        opened then `WasmtimeError` is raised.
        """

        res = ffi.wasi_config_set_stdin_file(
            self.ptr(), c_char_p(_encode_path(path)))
        if not res:
            raise WasmtimeError("failed to set stdin file")

    def inherit_stdin(self) -> None:
        """
        Configures this own process's stdin to be used as the WASI program's
        stdin.

        Reads of the stdin stream will read this process's stdin.
        """
        ffi.wasi_config_inherit_stdin(self.ptr())

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
            self.ptr(), c_char_p(_encode_path(path)))
        if not res:
            raise WasmtimeError("failed to set stdout file")

    def inherit_stdout(self) -> None:
        """
        Configures this own process's stdout to be used as the WASI program's
        stdout.

        Writes to stdout stream will write to this process's stdout.
        """
        ffi.wasi_config_inherit_stdout(self.ptr())

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
            self.ptr(), c_char_p(_encode_path(path)))
        if not res:
            raise WasmtimeError("failed to set stderr file")

    def inherit_stderr(self) -> None:
        """
        Configures this own process's stderr to be used as the WASI program's
        stderr.

        Writes to stderr stream will write to this process's stderr.
        """
        ffi.wasi_config_inherit_stderr(self.ptr())

    def preopen_dir(self, path: str, guest_path: str, dir_perms: DirPerms = DirPerms.READ_WRITE, file_perms: FilePerms = FilePerms.READ_WRITE) -> None:
        """
        Allows the WASI program to access the directory at `path` using the
        path `guest_path` within the WASI program.

        `dir_perms` specifies the permissions that wasm will have to operate on
        `guest_path`. This can be used, for example, to provide readonly access to a
        directory.

        `file_perms` specifies the maximum set of permissions that can be used for
        any file in this directory.
        """
        path_ptr = c_char_p(path.encode('utf-8'))
        guest_path_ptr = c_char_p(guest_path.encode('utf-8'))
        if not ffi.wasi_config_preopen_dir(self.ptr(), path_ptr, guest_path_ptr, dir_perms.value, file_perms.value):
            raise WasmtimeError('failed to add preopen dir')


def to_char_array(strings: List[str]) -> "ctypes._Pointer[ctypes._Pointer[c_char]]":
    ptrs = (c_char_p * len(strings))()
    for i, s in enumerate(strings):
        ptrs[i] = c_char_p(s.encode('utf-8'))
    return cast(ptrs, POINTER(POINTER(c_char)))
