from abc import ABC
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.storage.storage import MemoryValue, ReturnDataValue


@dataclass
class StorageWrite(ABC):
    pass


@dataclass
class StorageAccess(ABC):
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
    memory: Sequence[MemoryWrite] = ()
    return_data: ReturnWrite | None = None


@dataclass
class StorageAccesses:
    memory: Sequence[MemoryAccess] = ()
