__all__ = (
    "Exportable",
)

import typing

from ._func import Func
from ._globals import Global
from ._memory import Memory
from ._table import Table

Exportable = typing.Union[Func, Table, Memory, Global]
