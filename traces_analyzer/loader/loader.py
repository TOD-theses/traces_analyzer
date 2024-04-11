from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


# TODO: better naming / structure
@dataclass
class TransactionBundle:
    caller: str
    to: str
    hash: str
    calldata: str
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
