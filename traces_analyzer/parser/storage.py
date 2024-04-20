from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from typing_extensions import override


class StorageKey(ABC):
    pass


class StorageValue(ABC):
    pass


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
class MemoryRange(StorageKey):
    offset: int
    size: int


@dataclass
class MemoryValue(StorageValue):
    value: str


class MemoryStorage(Storage[MemoryRange, MemoryValue]):
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
    def get(self, key: MemoryRange) -> MemoryValue:
        memory = self.current_memory()
        offset = key.offset * 2
        to = offset + (key.size * 2)
        if offset < 0 or offset >= len(memory) or to < 0 or to >= len(memory):
            raise Exception(
                f"Memory range goes outside of memory. Tried to access memory[{offset/2}:{to/2}] "
                f"but memory has size {len(memory)/2}."
            )
        return MemoryValue(self.current_memory()[offset:to])

    def get_all(self) -> MemoryValue:
        return MemoryValue(self.current_memory())

    def set(self, offset: int, value: MemoryValue):
        data = value.value
        self.memory_stack[-1] = self.memory_stack[-1][:offset] + data + self.memory_stack[-1][offset + len(data) + 1 :]
