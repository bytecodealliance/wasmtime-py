import typing

if typing.TYPE_CHECKING:
    from ._func import Func
    from ._globals import Global
    from ._memory import Memory
    from ._table import Table
    from ._module import Module
    from ._instance import Instance

AsExtern = typing.Union["Func", "Table", "Memory", "Global", "Instance", "Module"]
