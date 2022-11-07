"""
Python bindings for the [Wasmtime project]

[Wasmtime project]: https://github.com/bytecodealliance/wasmtime

This library binds the [Wasmtime project]'s C API to provide an implementation
of a WebAssembly JIT compiler to Python. You can validate, compile, instantiate,
and interact with WebAssembly modules via this library.

The API of this library is intended to be very similar to the [`wasmtime` Rust
crate](https://docs.rs/wasmtime), so if you find the docs are lacking here feel
free to consult that documentation as well. While not exactly the same the two
libraries are intended to be quite similar.
"""

from ._error import WasmtimeError, ExitTrap
from ._config import Config
from ._engine import Engine
from ._store import Store, Storelike
from ._types import FuncType, GlobalType, MemoryType, TableType
from ._types import ValType, Limits, ImportType, ExportType
from ._wat2wasm import wat2wasm
from ._module import Module
from ._value import Val, IntoVal
from ._trap import Trap, Frame, TrapCode
from ._func import Func, Caller
from ._globals import Global
from ._table import Table
from ._memory import Memory
from ._instance import Instance
from ._wasi import WasiConfig
from ._linker import Linker

__all__ = [
    'wat2wasm',
    'Config',
    'Engine',
    'Store',
    'FuncType',
    'GlobalType',
    'MemoryType',
    'TableType',
    'ValType',
    'Limits',
    'ImportType',
    'ExportType',
    'IntoVal',
    'Val',
    'Func',
    'Caller',
    'Table',
    'Memory',
    'Global',
    'Trap',
    'TrapCode',
    'ExitTrap',
    'Frame',
    'Module',
    'Instance',
    'WasiConfig',
    'Linker',
    'WasmtimeError',
]
