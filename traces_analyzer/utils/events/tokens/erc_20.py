from typing import Sequence
from traces_parser.datatypes.hexstring import HexString
from typing_extensions import override, Self
from traces_analyzer.features.extractors.currency_changes import (
    CURRENCY_TYPE,
    CurrencyChange,
)
from traces_analyzer.utils.events.event import CurrencyChangeEvent


class ERC20TransferEvent(CurrencyChangeEvent):
    def __init__(
        self,
        sender: HexString,
        to: HexString,
        value: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.sender = sender
        self.to = to
        self.value = value.as_int()
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # Transfer(address indexed _from, address indexed _to, uint256 _value)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        return HexString(
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

    @override
    @classmethod
    def can_decode(cls, topics: Sequence[HexString], data: HexString) -> bool:
        return len(topics) == 3 and topics[0] == cls.signature()

    @override
    @classmethod
    def decode(
        cls, topics: Sequence[HexString], data: HexString, storage_address: HexString
    ) -> Self:
        return cls(
            topics[1].as_address(), topics[2].as_address(), data, storage_address
        )

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        return [
            CurrencyChange(
                type=CURRENCY_TYPE.ERC20,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.sender.with_prefix(),
                change=-self.value,
            ),
            CurrencyChange(
                type=CURRENCY_TYPE.ERC20,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.to.with_prefix(),
                change=self.value,
            ),
        ]
