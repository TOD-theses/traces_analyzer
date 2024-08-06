from typing import Sequence
from typing_extensions import Self
from traces_parser.datatypes.hexstring import HexString
from abc import abstractmethod

from traces_analyzer.features.extractors.currency_changes import CurrencyChange


class Event:
    @staticmethod
    @abstractmethod
    def signature() -> HexString:
        pass

    @classmethod
    @abstractmethod
    def can_decode(cls, topics: Sequence[HexString], data: HexString) -> bool:
        pass

    @classmethod
    @abstractmethod
    def decode(
        cls, topics: Sequence[HexString], data: HexString, storage_address: HexString
    ) -> Self:
        pass


class CurrencyChangeEvent(Event):
    @abstractmethod
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        pass
