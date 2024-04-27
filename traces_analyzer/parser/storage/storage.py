from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

from typing_extensions import override


class StorageKey(ABC):
    pass


class StorageValue(ABC):

    @abstractmethod
    def get_hexstring(self) -> str:
        pass


@dataclass
class HexStringStorageValue(StorageValue):
    hexstring: str

    def is_concrete(self) -> bool:
        return True

    def get_hexstring(self) -> str:
        return self.hexstring


Key = TypeVar("Key", bound=StorageKey)
Value = TypeVar("Value", bound=StorageValue)


class Storage(ABC, Generic[Key, Value]):
    """
    Types of storage:
    - stack, memory => current call context as key (or stack based)
    - persistent/transient storage => address as key
    - balance, code => address as key
    - calldata, call value, return data => current or previous call context as a key
    """

    def on_call_enter(self):
        pass

    def on_call_exit(self):
        pass

    @abstractmethod
    def get(self, key: Key) -> Value:
        pass


@dataclass
class StackIndex(StorageKey):
    index: int


class StackStorage(Storage[StackIndex, HexStringStorageValue]):
    def __init__(self) -> None:
        super().__init__()
        self.stacks: list[list[str]] = [[]]

    @override
    def on_call_enter(self):
        super().on_call_enter()
        self.stacks.append([])

    @override
    def on_call_exit(self):
        super().on_call_exit()
        self.stacks.pop()

    @override
    def get(self, key: StackIndex) -> HexStringStorageValue:
        """Get the nth element from the top of the stack (0-indexed)"""
        stack = self.current_stack()
        return HexStringStorageValue(stack[-key.index - 1])

    def push(self, value: HexStringStorageValue):
        """Push a single value to the top of the stack"""
        self.current_stack().append(value.get_hexstring())

    def push_all(self, values: Sequence[HexStringStorageValue]):
        """Push multiple values. First one will be on top of the stack"""
        for value in reversed(values):
            self.push(value)

    def pop_n(self, n: int):
        """Pop and return the top n stack items"""
        results = [self.get(StackIndex(i)) for i in range(n)]
        del self.current_stack()[-n:]
        return results

    def clear(self):
        self.stacks[-1] = []

    def current_stack(self) -> list[str]:
        return self.stacks[-1]


@dataclass
class MemoryRange(StorageKey):
    offset: int
    size: int


def mem_pad_with_leading_zeros(value: str) -> str:
    if len(value) % (32 * 2) == 0:
        return value
    return "0" * (32 * 2 - (len(value) % (32 * 2))) + value


class MemoryStorage(Storage[MemoryRange, HexStringStorageValue]):
    def __init__(self) -> None:
        super().__init__()
        self.memory_stack: list[str] = [""]

    @override
    def on_call_enter(self):
        super().on_call_enter()
        self.memory_stack.append("")

    @override
    def on_call_exit(self):
        super().on_call_exit()
        self.memory_stack.pop()

    def current_memory(self) -> str:
        return self.memory_stack[-1]

    @override
    def get(self, key: MemoryRange) -> HexStringStorageValue:
        """Get memory range. Return 0s if accessing out of range memory, without expanding"""
        offset = key.offset * 2
        size = key.size * 2
        current_memory = self.current_memory()
        slice = current_memory[offset : offset + size]
        slice = slice.ljust(size, "0")
        return HexStringStorageValue(slice)

    def get_all(self) -> HexStringStorageValue:
        return HexStringStorageValue(self.current_memory())

    def set(self, offset: int, value: HexStringStorageValue):
        if not value.get_hexstring():
            return
        data = value.get_hexstring()
        self.check_expansion(offset, len(data) // 2)
        mem = self.memory_stack[-1]
        self.memory_stack[-1] = mem[: offset * 2] + data + mem[offset * 2 + len(data) :]

    def check_expansion(self, offset: int, size: int):
        if size == 0:
            return
        while self.size() < offset + size:
            self._expand()

    def _expand(self):
        self.memory_stack[-1] = self.memory_stack[-1] + "00" * 32

    def size(self) -> int:
        return len(self.memory_stack[-1]) // 2
