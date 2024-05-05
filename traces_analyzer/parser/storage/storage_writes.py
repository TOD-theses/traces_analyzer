from abc import ABC
from dataclasses import dataclass
from typing import Iterable, Sequence

from traces_analyzer.parser.storage.storage_value import StorageByteGroup


@dataclass
class StorageWrite(ABC):
    pass


@dataclass
class StorageAccess(ABC):
    pass


@dataclass
class StackAccess(StorageAccess):
    index: int
    value: StorageByteGroup


@dataclass
class StackSet(StorageWrite):
    index: int
    value: StorageByteGroup


@dataclass
class StackPush(StorageWrite):
    value: StorageByteGroup


@dataclass
class StackPop(StorageWrite):
    pass


@dataclass
class MemoryWrite(StorageWrite):
    offset: int
    value: StorageByteGroup


@dataclass
class MemoryAccess(StorageAccess):
    offset: int
    value: StorageByteGroup


@dataclass
class ReturnWrite(StorageWrite):
    value: StorageByteGroup


@dataclass
class ReturnDataAccess(StorageAccess):
    offset: int
    size: int
    value: StorageByteGroup


@dataclass
class BalanceAccess(StorageAccess):
    address: StorageByteGroup
    last_modified_step_index: int


@dataclass
class StorageWrites:
    stack_sets: Sequence[StackSet] = ()
    stack_pops: Sequence[StackPop] = ()
    stack_pushes: Sequence[StackPush] = ()
    memory: Sequence[MemoryWrite] = ()
    return_data: ReturnWrite | None = None


@dataclass
class StorageAccesses:
    stack: Sequence[StackAccess] = ()
    memory: Sequence[MemoryAccess] = ()
    balance: Sequence[BalanceAccess] = ()
    return_data: ReturnDataAccess | None = None

    def get_dependencies(self) -> Iterable[tuple[int, StorageAccess, StorageByteGroup | None]]:
        # TODO: unit test
        for stack_access in self.stack:
            for group in stack_access.value.split_by_dependencies():
                step_index = next(iter(group.depends_on_instruction_indexes()))
                yield (step_index, stack_access, group)

        for memory_access in self.memory:
            for group in memory_access.value.split_by_dependencies():
                step_index = next(iter(group.depends_on_instruction_indexes()))
                yield (step_index, memory_access, group)

        for balance_access in self.balance:
            yield (balance_access.last_modified_step_index, balance_access, None)

        if self.return_data:
            for group in self.return_data.value.split_by_dependencies():
                step_index = next(iter(group.depends_on_instruction_indexes()))
                yield (step_index, self.return_data, group)
