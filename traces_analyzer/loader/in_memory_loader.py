from typing import Generic, TypeVar
from traces_analyzer.loader.event_parser import EventsParser
from traces_analyzer.loader.loader import PotentialAttack, TraceBundle, TraceLoader
from traces_analyzer.loader.types import TxData

from traces_parser.datatypes.hexstring import HexString

T = TypeVar("T")


class InMemoryLoader(TraceLoader, Generic[T]):
    def __init__(
        self,
        id: str,
        tx: TxData,
        data_normal: T,
        data_reverse: T,
        parser: EventsParser[T],
    ) -> None:
        self.id = id
        self.tx = tx
        self.events_normal = parser.parse(data_normal)
        self.events_reverse = parser.parse(data_reverse)

    def __enter__(self) -> PotentialAttack:
        return PotentialAttack(
            id=self.id,
            tx_victim=TraceBundle(
                hash=HexString(self.tx["hash"]),
                caller=HexString(self.tx["from"]),
                to=HexString(self.tx["to"]),
                calldata=HexString(self.tx["input"]),
                value=HexString(self.tx["value"]),
                events_normal=self.events_normal,
                events_reverse=self.events_reverse,
            ),
        )

    def __exit__(self, exc_type, exc_value, traceback):
        pass
