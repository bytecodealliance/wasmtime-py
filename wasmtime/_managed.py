from abc import abstractmethod
from typing import TypeVar, Generic, Any, Optional

T = TypeVar('T')

class Managed(Generic[T]):
    """
    Abstract base class for types which contain an owned pointer in the C FFI
    layer.

    Not exported directly from this package.
    """
    __ptr: Optional[T]

    @abstractmethod
    def _delete(self, ptr: T) -> None:
        """
        Runs the FFI destructor for the `ptr` specified.

        Must be implemented by classes that inherit from this class.
        """
        pass

    def _set_ptr(self, ptr: T) -> None:
        if hasattr(self, '__ptr'):
            raise ValueError('already initialized')
        self.__ptr = ptr

    def close(self) -> None:
        """
        Closes this object, or deallocates it. Further usage of this object
        will raise a `ValueError`.
        """

        # Get the pointer's value but don't worry if it was never set.
        try:
            ptr = self.__ptr
        except AttributeError:
            return

        # If it wasn't previously deallocated then do so here, otherwise ignore
        # this repeated call to `close`
        if ptr is not None:
            self._delete(ptr)
            self.__ptr = None

    def ptr(self) -> T:
        """
        Returns the underlying pointer for this FFI object, or a `ValueError`
        if it's already been closed.
        """

        # Fail with a `ValueError` if the pointer was never set
        try:
            ptr = self.__ptr
        except AttributeError:
            raise ValueError('never initialized')

        # Check to see if this object is already deallocated, and if so raise
        # a specific exception
        if ptr is not None:
            return ptr
        else:
            raise ValueError('already closed')

    def _consume(self) -> T:
        """
        Internal method to take ownership of the internal pointer without
        destroying it.
        """
        ret = self.ptr()
        self.__ptr = None
        return ret

    def __enter__(self) -> Any:
        """
        Entry part of the contextlib protocol to enable using this object with
        `with`.

        Returns `self` to bind to use within a `with` block.
        """
        return self

    def __exit__(self, *exc: Any) -> None:
        """
        Exit part of the contextlib protocol to call `close`.
        """
        self.close()

    def __del__(self) -> None:
        """
        Automatic destruction of the internal FFI object if it's still alive by
        this point.
        """
        self.close()
