from typing import Generic, List, Union, cast, TypeVar


T = TypeVar('T')


class Slab(Generic[T]):
    list: List[Union[int, T]]
    next: int

    def __init__(self) -> None:
        self.list = []
        self.next = 0

    def allocate(self, val: T) -> int:
        idx = self.next

        if len(self.list) == idx:
            self.list.append(0)
            self.next += 1
        else:
            self.next = cast(int, self.list[idx])

        self.list[idx] = val
        return idx

    def get(self, idx: int) -> T:
        return cast(T, self.list[idx])

    def deallocate(self, idx: int) -> None:
        self.list[idx] = self.next
        self.next = idx
