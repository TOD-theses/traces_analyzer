from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from traces_parser.datatypes import HexString
from traces_parser.parser.events_parser import TraceEvent


@dataclass
class TraceBundle:
    """Traces of the same transaction in two orders"""

    hash: HexString
    caller: HexString
    to: HexString
    calldata: HexString
    value: HexString
    events_normal: Iterable[TraceEvent]
    events_reverse: Iterable[TraceEvent]


@dataclass
class PotentialAttack:
    id: str
    tx_a: TraceBundle
    tx_b: TraceBundle


class TraceLoader(ABC):
    @abstractmethod
    def __enter__(self) -> PotentialAttack:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass
