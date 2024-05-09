from .generated import Root, RootImports, Err, imports
from .generated.imports import streams
from .generated.imports.types import Descriptor, Filesize, ErrorCode, DescriptorType
from .generated.imports.terminal_input import TerminalInput
from .generated.imports.terminal_output import TerminalOutput
from .generated.imports import terminal_stderr
from .generated import types as core_types
from typing import Mapping, Tuple, List, Optional

import sys
import os
from wasmtime import Store


class WasiRandom(imports.HostRandom):
    def get_random_bytes(self, len: int) -> bytes:
        return os.urandom(len)


class WasiStdin(imports.HostStdin):
    def get_stdin(self) -> streams.InputStream:
        return 0


class WasiStdout(imports.HostStdout):
    def get_stdout(self) -> streams.OutputStream:
        return 1


class WasiStderr(imports.HostStderr):
    def get_stderr(self) -> streams.OutputStream:
        return 2


class WasiPreopens(imports.HostPreopens):
    def get_directories(self) -> List[Tuple[Descriptor, str]]:
        return []


class WasiStreams(imports.HostStreams):
    def drop_input_stream(self, this: streams.InputStream) -> None:
        return None

    def write(self, this: streams.OutputStream, buf: bytes) -> core_types.Result[Tuple[int, streams.StreamStatus], None]:
        if this == 1:
            sys.stdout.buffer.write(buf)
        elif this == 2:
            sys.stderr.buffer.write(buf)
        else:
            raise NotImplementedError
        return core_types.Ok((len(buf), streams.StreamStatus.OPEN))

    def blocking_write(self, this: streams.OutputStream, buf: bytes) -> core_types.Result[Tuple[int, streams.StreamStatus], None]:
        return self.write(this, buf)

    def drop_output_stream(self, this: streams.OutputStream) -> None:
        return None


class WasiEnvironment(imports.HostEnvironment):
    def get_environment(self) -> List[Tuple[str, str]]:
        return []


class WasiTypes(imports.HostTypes):
    def write_via_stream(self, this: Descriptor, offset: Filesize) -> core_types.Result[streams.OutputStream, ErrorCode]:
        raise NotImplementedError

    def append_via_stream(self, this: Descriptor) -> core_types.Result[streams.OutputStream, ErrorCode]:
        raise NotImplementedError

    def get_type(self, this: Descriptor) -> core_types.Result[DescriptorType, ErrorCode]:
        raise NotImplementedError

    def drop_descriptor(self, this: Descriptor) -> None:
        raise NotImplementedError


class WasiExit(imports.HostExit):
    def exit(self, status: core_types.Result[None, None]) -> None:
        raise NotImplementedError


class WasiTerminalInput(imports.HostTerminalInput):
    def drop_terminal_input(self, this: TerminalInput) -> None:
        pass


class WasiTerminalOutput(imports.HostTerminalOutput):
    def drop_terminal_output(self, this: TerminalOutput) -> None:
        pass


class WasiTerminalStdin(imports.HostTerminalStdin):
    def get_terminal_stdin(self) -> Optional[TerminalInput]:
        if sys.stdin.isatty():
            return sys.stdin.fileno()
        return None


class WasiTerminalStdout(imports.HostTerminalStdout):
    def get_terminal_stdout(self) -> Optional[TerminalOutput]:
        if sys.stdout.isatty():
            return sys.stdout.fileno()
        return None


class WasiTerminalStderr(imports.HostTerminalStderr):
    def get_terminal_stderr(self) -> Optional[terminal_stderr.TerminalOutput]:
        if sys.stderr.isatty():
            return sys.stderr.fileno()
        return None


root = None
store = None


def init() -> Tuple[Root, Store]:
    global store
    global root
    if root is None:
        store = Store()
        root = Root(store, RootImports(WasiStreams(),
                                       WasiTypes(),
                                       WasiPreopens(),
                                       WasiRandom(),
                                       WasiEnvironment(),
                                       WasiExit(),
                                       WasiStdin(),
                                       WasiStdout(),
                                       WasiStderr(),
                                       WasiTerminalInput(),
                                       WasiTerminalOutput(),
                                       WasiTerminalStdin(),
                                       WasiTerminalStdout(),
                                       WasiTerminalStderr()))
    return root, store


# Generates Python bindings for the given component.
#
# The `name` provided is used as the name of the `component` binary provided.
# The `component` argument is expected to be the binary representation of a
# component.
#
# This function returns a mapping of filename to contents of files that are
# generated to represent the Python bindings here.
def generate(name: str, component: bytes) -> Mapping[str, bytes]:
    root, store = init()
    result = root.generate(store, name, component)
    if isinstance(result, Err):
        raise RuntimeError(result.value)
    ret = {}
    for name, contents in result.value:
        ret[name] = contents
    return ret


__all__ = ['generate']
