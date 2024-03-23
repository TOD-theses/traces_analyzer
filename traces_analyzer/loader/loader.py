from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


# TODO: how do I analyze 4 traces? Currently I only compare two traces
# TODO: better naming / structure
@dataclass
class TransactionBundle:
    caller: str
    to: str
    hash: str
    trace_one: Iterable[str]
    trace_two: Iterable[str]


@dataclass
class TraceBundle:
    id: str
    tx_victim: TransactionBundle
    tx_attack: TransactionBundle


class TraceLoader(ABC):
    @abstractmethod
    def load(self) -> TraceBundle:
        pass
