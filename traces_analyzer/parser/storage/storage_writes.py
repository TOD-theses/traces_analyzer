from abc import ABC
from dataclasses import dataclass
from typing import Sequence

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
    # TODO: wrap it to allow information flow analysis
    value: StorageByteGroup


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
