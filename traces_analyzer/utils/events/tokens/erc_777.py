from typing import Sequence
from traces_parser.datatypes.hexstring import HexString
from typing_extensions import override, Self
from traces_analyzer.features.extractors.currency_changes import (
    CURRENCY_TYPE,
    CurrencyChange,
)
from traces_analyzer.utils.events.event import CurrencyChangeEvent


class ERC777SentEvent(CurrencyChangeEvent):
    def __init__(
        self,
        sender: HexString,
        to: HexString,
        amount: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.sender = sender
        self.to = to
        self.value = amount.as_int()
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # Sent(address indexed operator,address indexed from,address indexed to,uint256 amount,bytes data,bytes operatorData)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0x06b541ddaa720db2b10a4d0cdac39b8d360425fc073085fac19bc82614677987
        return HexString(
            "0x06b541ddaa720db2b10a4d0cdac39b8d360425fc073085fac19bc82614677987"
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
            topics[2].as_address(), topics[3].as_address(), data[:64], storage_address
        )

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        return [
            CurrencyChange(
                type=CURRENCY_TYPE.ERC777,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.sender.with_prefix(),
                change=-self.value,
            ),
            CurrencyChange(
                type=CURRENCY_TYPE.ERC777,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.to.with_prefix(),
                change=self.value,
            ),
        ]


class ERC777MintedEvent(CurrencyChangeEvent):
    def __init__(
        self,
        to: HexString,
        amount: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.to = to
        self.value = amount.as_int()
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # Minted(address indexed operator, address indexed to, uint256 amount, bytes data, bytes operatorData)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0x2fe5be0146f74c5bce36c0b80911af6c7d86ff27e89d5cfa61fc681327954e5d
        return HexString(
            "0x2fe5be0146f74c5bce36c0b80911af6c7d86ff27e89d5cfa61fc681327954e5d"
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
        return cls(topics[2].as_address(), data[:64], storage_address)

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        return [
            CurrencyChange(
                type=CURRENCY_TYPE.ERC777,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.to.with_prefix(),
                change=self.value,
            ),
        ]


class ERC777BurnedEvent(CurrencyChangeEvent):
    def __init__(
        self,
        to: HexString,
        amount: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.holder = to
        self.value = amount.as_int()
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # Minted(address indexed operator, address indexed from, uint256 amount, bytes data, bytes operatorData)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0xa78a9be3a7b862d26933ad85fb11d80ef66b8f972d7cbba06621d583943a4098
        return HexString(
            "0xa78a9be3a7b862d26933ad85fb11d80ef66b8f972d7cbba06621d583943a4098"
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
        return cls(topics[2].as_address(), data[:64], storage_address)

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        return [
            CurrencyChange(
                type=CURRENCY_TYPE.ERC777,
                currency_identifier=self.token_address.with_prefix(),
                owner=self.holder.with_prefix(),
                change=-self.value,
            ),
        ]
