from abc import ABC
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.storage.storage import HexStringStorageValue


@dataclass
class StorageWrite(ABC):
    pass


@dataclass
class StorageAccess(ABC):
    pass


@dataclass
class StackAccess(StorageAccess):
    index: int
    value: HexStringStorageValue


@dataclass
class StackSet(StorageWrite):
    index: int
    value: HexStringStorageValue


@dataclass
class StackPush(StorageWrite):
    value: HexStringStorageValue


@dataclass
class StackPop(StorageWrite):
    pass


@dataclass
class MemoryWrite(StorageWrite):
    offset: int
    value: HexStringStorageValue


@dataclass
class MemoryAccess(StorageAccess):
    offset: int
    value: HexStringStorageValue


@dataclass
class ReturnWrite(StorageWrite):
    # TODO: wrap it to allow information flow analysis
    value: HexStringStorageValue


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
