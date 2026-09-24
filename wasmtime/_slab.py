import itertools
from typing import Dict, Generic, Iterator, TypeVar


T = TypeVar('T')


class Slab(Generic[T]):
    """Maps integer handles to Python objects, safe to use from many threads.

    Wasmtime objects release their handles from finalizers, and the garbage
    collector runs finalizers on whichever thread happens to trigger a
    collection. An application that uses wasmtime from one thread can
    therefore see `deallocate` run on another thread, concurrently with
    `allocate`.

    Handles come from a monotonically increasing counter and are never reused,
    and the values live in a dict, so there is no free list whose invariant
    spans several statements for a concurrent call to break. Every step is a
    single `next()` or dict operation, which the GIL makes atomic, so no lock
    is needed, and a finalizer that frees another handle mid-call cannot
    deadlock or see a half-updated slab.
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
        # Idempotent: freeing a handle twice, or freeing one that was never
        # handed out, leaves the live handles alone.
        self.handles.pop(idx, None)
