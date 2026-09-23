import sys
import threading
import unittest

from wasmtime._slab import Slab


class TestSlab(unittest.TestCase):
    def test_concurrent_allocate_and_deallocate(self):
        """Handles stay unique and keep their values across threads.

        The garbage collector runs wasmtime finalizers, and so `deallocate`, on
        whichever thread triggers a collection, concurrently with `allocate` on
        the thread that is using wasmtime.
        """
        slab: Slab[object] = Slab()
        threads = 8
        iterations = 20000
        barrier = threading.Barrier(threads)
        errors = []

        def worker(n):
            try:
                barrier.wait()
                live = {}
                for i in range(iterations):
                    val = (n, i)
                    live[slab.allocate(val)] = val
                    if len(live) > 4:
                        idx = next(iter(live))
                        if slab.get(idx) is not live.pop(idx):
                            raise AssertionError(
                                'handle {} was handed to two owners'.format(idx))
                        slab.deallocate(idx)
            except BaseException as e:
                errors.append(e)

        interval = sys.getswitchinterval()
        # Switch threads as often as possible to provoke interleavings.
        sys.setswitchinterval(1e-6)
        try:
            workers = [threading.Thread(target=worker, args=(n,))
                       for n in range(threads)]
            for t in workers:
                t.start()
            for t in workers:
                t.join()
        finally:
            sys.setswitchinterval(interval)

        self.assertEqual(errors, [])
