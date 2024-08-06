from typing import Sequence
from traces_parser.datatypes.hexstring import HexString
from typing_extensions import override, Self
from traces_analyzer.features.extractors.currency_changes import (
    CURRENCY_TYPE,
    CurrencyChange,
)
from traces_analyzer.utils.events.event import CurrencyChangeEvent


class ERC721TransferEvent(CurrencyChangeEvent):
    def __init__(
        self,
        sender: HexString,
        to: HexString,
        token_id: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.sender = sender
        self.to = to
        self.token_id = token_id
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # Transfer(address indexed _from, address indexed _to, uint256 indexed _tokenId)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        return HexString(
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

    @override
    @classmethod
    def can_decode(cls, topics: Sequence[HexString], data: HexString) -> bool:
        return len(topics) == 4 and topics[0] == cls.signature()

    @override
    @classmethod
    def decode(
        cls, topics: Sequence[HexString], data: HexString, storage_address: HexString
    ) -> Self:
        return cls(
            topics[1].as_address(), topics[2].as_address(), topics[3], storage_address
        )

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        id = f"{self.token_address.with_prefix()}-{self.token_id.with_prefix()}"
        return [
            CurrencyChange(
                type=CURRENCY_TYPE.ERC721,
                currency_identifier=id,
                owner=self.sender.with_prefix(),
                change=-1,
            ),
            CurrencyChange(
                type=CURRENCY_TYPE.ERC721,
                currency_identifier=id,
                owner=self.to.with_prefix(),
                change=1,
            ),
        ]
