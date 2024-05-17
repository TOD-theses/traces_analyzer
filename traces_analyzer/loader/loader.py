from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from traces_analyzer.utils.hexstring import HexString


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
    tx_attack: TraceBundle


class TraceLoader(ABC):
    @abstractmethod
    def load(self) -> PotentialAttack:
        pass
