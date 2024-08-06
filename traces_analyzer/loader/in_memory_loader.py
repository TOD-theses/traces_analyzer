from typing import Generic, Iterable, TypeVar
from traces_analyzer.loader.event_parser import EventsParser
from traces_analyzer.loader.loader import PotentialAttack, TraceBundle, TraceLoader
from traces_analyzer.loader.types import TxData

from traces_parser.datatypes.hexstring import HexString
from traces_parser.parser.events_parser import TraceEvent

T = TypeVar("T")


class InMemoryLoader(TraceLoader, Generic[T]):
    def __init__(
        self,
        id: str,
        tx_a: TxData,
        tx_b: TxData,
        tx_a_data_normal: T,
        tx_a_data_reverse: T,
        tx_b_data_normal: T,
        tx_b_data_reverse: T,
        parser: EventsParser[T],
    ) -> None:
        self.id = id
        self.tx_a = tx_a
        self.tx_b = tx_b
        self.events_a_normal = parser.parse(tx_a_data_normal)
        self.events_a_reverse = parser.parse(tx_a_data_reverse)
        self.events_b_normal = parser.parse(tx_b_data_normal)
        self.events_b_reverse = parser.parse(tx_b_data_reverse)

    def __enter__(self) -> PotentialAttack:
        return PotentialAttack(
            id=self.id,
            tx_a=self._load_bundle(
                self.tx_a, self.events_a_normal, self.events_a_reverse
            ),
            tx_b=self._load_bundle(
                self.tx_b, self.events_b_normal, self.events_b_reverse
            ),
        )

    def _load_bundle(
        self,
        tx: TxData,
        events_normal: Iterable[TraceEvent],
        events_reverse: Iterable[TraceEvent],
    ) -> TraceBundle:
        return TraceBundle(
            hash=HexString(tx["hash"]),
            caller=HexString(tx["from"]),
            to=HexString(tx["to"]),
            calldata=HexString(tx["input"]),
            value=HexString(tx["value"]),
            events_normal=events_normal,
            events_reverse=events_reverse,
        )

    def __exit__(self, exc_type, exc_value, traceback):
        pass
