import typing

if typing.TYPE_CHECKING:
    from ._func import Func
    from ._globals import Global
    from ._memory import Memory
    from ._sharedmemory import SharedMemory
    from ._table import Table

AsExtern = typing.Union["Func", "Table", "Memory", "SharedMemory",  "Global"]
