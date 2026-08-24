import gc
import unittest

from wasmtime._slab import Slab


class TestSlab(unittest.TestCase):
    def test_allocate_get_deallocate(self):
        slab: Slab[str] = Slab()

        idx = slab.allocate('a')

        self.assertEqual(slab.get(idx), 'a')
        slab.deallocate(idx)
        # A freed handle fails loudly rather than resolving to whatever the
        # storage happens to hold at that index.
        with self.assertRaises(KeyError):
            slab.get(idx)

    def test_handles_are_never_zero(self):
        # Callers round-trip a handle through a C `void *` and read a null one
        # back as `idx or 0` (see `_func.py`, `_wasi.py`, `component/_linker.py`),
        # so a handle of 0 cannot be told apart from an absent one. `_value.py`
        # already works around this by hand with a +1/-1 offset.
        slab: Slab[str] = Slab()

        self.assertNotEqual(slab.allocate('a'), 0)

    def test_handles_are_not_reused(self):
        slab: Slab[str] = Slab()

        first = slab.allocate('a')
        slab.deallocate(first)

        self.assertNotEqual(slab.allocate('b'), first)

    def test_double_free_leaves_live_handles_alone(self):
        """A handle freed twice must not disturb the handles still in use.

        `deallocate` runs from a C finalizer that reads a null `void *` as
        handle 0, so a slab can be asked to free something it never handed out.
        With a free list threaded through the storage, that pointed the head at
        a slot that was still live, the next two allocations both returned it,
        and the one after raised `TypeError: list indices must be integers or
        slices, not tuple`.
        """
        slab: Slab[str] = Slab()
        live = {}
        for i in range(3):
            live[slab.allocate('keeper-{}'.format(i))] = 'keeper-{}'.format(i)
        victim = slab.allocate('victim')

        slab.deallocate(victim)
        slab.deallocate(victim)

        for i in range(3):
            live[slab.allocate('fresh-{}'.format(i))] = 'fresh-{}'.format(i)

        for idx, val in live.items():
            self.assertEqual(slab.get(idx), val)

    def test_deallocating_a_handle_can_free_another(self):
        """Dropping a value can free a second handle before the first call returns.

        A slab usually holds the only reference to its value, so freeing one
        handle runs that value's `__del__`, which can free another handle. On
        CPython that lands inside the outer `deallocate`. Anything added to
        guard these methods has to tolerate it: a plain `threading.Lock` around
        `deallocate` deadlocks here.
        """
        slab: Slab[object] = Slab()

        class FreesAnotherHandleWhenDropped:
            def __init__(self, frees):
                self.frees = frees

            def __del__(self):
                if self.frees is not None:
                    slab.deallocate(self.frees)

        inner = slab.allocate(FreesAnotherHandleWhenDropped(None))
        outer = slab.allocate(FreesAnotherHandleWhenDropped(inner))

        slab.deallocate(outer)
        gc.collect()  # PyPy doesn't refcount, so force the drop.

        for idx in (outer, inner):
            with self.assertRaises(KeyError):
                slab.get(idx)
