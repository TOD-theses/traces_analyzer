from abc import ABC
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.storage.storage import MemoryValue, ReturnDataValue, StackValue


@dataclass
class StorageWrite(ABC):
    pass


@dataclass
class StorageAccess(ABC):
    pass

@dataclass
class StackAccess(StorageAccess):
    index: int
    value: StackValue

@dataclass
class StackSet(StorageWrite):
    index: int
    value: StackValue

@dataclass
class StackPush(StorageWrite):
    value: StackValue

@dataclass
class StackPop(StorageWrite):
    pass

@dataclass
class MemoryWrite(StorageWrite):
    offset: int
    value: MemoryValue


@dataclass
class MemoryAccess(StorageAccess):
    offset: int
    value: MemoryValue


@dataclass
class ReturnWrite(StorageWrite):
    # TODO: wrap it to allow information flow analysis
    value: ReturnDataValue


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
