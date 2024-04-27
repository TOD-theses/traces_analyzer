from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from traces_analyzer.utils.hexstring import HexString


# TODO: better naming / structure
@dataclass
class TransactionBundle:
    caller: HexString
    to: HexString
    hash: HexString
    calldata: HexString
    trace_actual: Iterable[str]
    trace_reverse: Iterable[str]


@dataclass
class TraceBundle:
    id: str
    tx_victim: TransactionBundle
    tx_attack: TransactionBundle


class TraceLoader(ABC):
    @abstractmethod
    def load(self) -> TraceBundle:
        pass
