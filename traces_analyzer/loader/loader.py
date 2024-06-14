from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from traces_parser.datatypes import HexString


@dataclass
class TraceBundle:
    """Traces of the same transaction in two orders"""

    hash: HexString
    caller: HexString
    to: HexString
    calldata: HexString
    value: HexString
    trace_actual: Iterable[str]
    trace_reverse: Iterable[str]


@dataclass
class PotentialAttack:
    id: str
    tx_victim: TraceBundle


class TraceLoader(ABC):
    @abstractmethod
    def __enter__(self) -> PotentialAttack:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass
