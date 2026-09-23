import itertools
import threading
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
    spans several statements for a concurrent call to break. The only lock
    guards the counter, and it is never held while a value is dropped, so a
    finalizer that frees another handle cannot deadlock on it.
    """

    handles: Dict[int, T]
    counter: Iterator[int]
    lock: threading.Lock

    def __init__(self) -> None:
        # Counting from 1, never 0: callers round-trip a handle through a C
        # `void *` and read a null one back as `idx or 0`, so a handle of 0 is
        # indistinguishable from an absent one.
        self.handles = {}
        self.counter = itertools.count(1)
        # `next()` on `itertools.count` is atomic under the GIL but not on
        # free-threaded builds.
        self.lock = threading.Lock()

    def allocate(self, val: T) -> int:
        with self.lock:
            idx = next(self.counter)
        self.handles[idx] = val
        return idx

    def get(self, idx: int) -> T:
        return self.handles[idx]

    def deallocate(self, idx: int) -> None:
        # Idempotent: freeing a handle twice, or freeing one that was never
        # handed out, leaves the live handles alone.
        self.handles.pop(idx, None)
