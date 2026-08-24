import itertools
from typing import Dict, Generic, Iterator, TypeVar


T = TypeVar('T')


class Slab(Generic[T]):
    """Maps integer handles to Python objects.

    Handles come from a monotonically increasing counter and are never reused,
    and the values live in a dict. Nothing is threaded through the storage, so
    there is no invariant spanning two operations for a stray free to break.
    """

    handles: Dict[int, T]
    counter: Iterator[int]

    def __init__(self) -> None:
        # Counting from 1, never 0: callers round-trip a handle through a C
        # `void *` and read a null one back as `idx or 0`, so a handle of 0 is
        # indistinguishable from an absent one.
        self.handles = {}
        self.counter = itertools.count(1)

    def allocate(self, val: T) -> int:
        idx = next(self.counter)
        self.handles[idx] = val
        return idx

    def get(self, idx: int) -> T:
        return self.handles[idx]

    def deallocate(self, idx: int) -> None:
        # Idempotent: freeing a handle twice, or freeing one the caller never
        # owned, must not disturb the handles that are still live.
        self.handles.pop(idx, None)
