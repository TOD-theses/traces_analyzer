from typing import Sequence
from traces_parser.datatypes.hexstring import HexString
from typing_extensions import override, Self
from traces_analyzer.features.extractors.currency_changes import (
    CURRENCY_TYPE,
    CurrencyChange,
)
from traces_analyzer.utils.events.event import CurrencyChangeEvent
from eth_abi.abi import decode


class ERC1155TransferSingleEvent(CurrencyChangeEvent):
    def __init__(
        self,
        sender: HexString,
        to: HexString,
        value: HexString,
        token_id: HexString,
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.sender = sender
        self.to = to
        self.value = value.as_int()
        self.token_id = token_id
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # TransferSingle(address indexed _operator, address indexed _from, address indexed _to, uint256 _id, uint256 _value)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62
        return HexString(
            "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
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
        id, value = decode(["uint256", "uint256"], bytes.fromhex(data.without_prefix()))
        return cls(
            topics[2].as_address(),
            topics[3].as_address(),
            HexString.from_int(value),
            HexString.from_int(id),
            storage_address,
        )

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        id = f"{self.token_address.with_prefix()}-{self.token_id.with_prefix()}"
        changes = []
        if self.sender.as_int() != 0:
            changes.append(
                CurrencyChange(
                    type=CURRENCY_TYPE.ERC1155,
                    currency_identifier=id,
                    owner=self.sender.with_prefix(),
                    change=-self.value,
                )
            )
        if self.to.as_int() != 0:
            changes.append(
                CurrencyChange(
                    type=CURRENCY_TYPE.ERC1155,
                    currency_identifier=id,
                    owner=self.to.with_prefix(),
                    change=self.value,
                )
            )
        return changes


class ERC1155TransferBatchEvent(CurrencyChangeEvent):
    def __init__(
        self,
        sender: HexString,
        to: HexString,
        values: Sequence[HexString],
        token_ids: Sequence[HexString],
        token_address: HexString,
    ) -> None:
        super().__init__()
        self.sender = sender
        self.to = to
        self.values = [v.as_int() for v in values]
        self.token_ids = token_ids
        self.token_address = token_address

    @override
    @staticmethod
    def signature() -> HexString:
        # TransferBatch(address indexed _operator, address indexed _from, address indexed _to, uint256[] _ids, uint256[] _values)
        # https://www.4byte.directory/event-signatures/?bytes_signature=0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb
        return HexString(
            "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
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
        ids, values = decode(
            ["uint256[]", "uint256[]"], bytes.fromhex(data.without_prefix())
        )
        ids = [HexString.from_int(id) for id in ids]
        values = [HexString.from_int(value) for value in values]
        return cls(
            topics[2].as_address(), topics[3].as_address(), values, ids, storage_address
        )

    @override
    def get_currency_changes(self) -> Sequence[CurrencyChange]:
        changes = []
        for value, token_id in zip(self.values, self.token_ids):
            id = f"{self.token_address.with_prefix()}-{token_id.with_prefix()}"
            if self.sender.as_int() != 0:
                changes.append(
                    CurrencyChange(
                        type=CURRENCY_TYPE.ERC1155,
                        currency_identifier=id,
                        owner=self.sender.with_prefix(),
                        change=-value,
                    )
                )
            if self.to.as_int() != 0:
                changes.append(
                    CurrencyChange(
                        type=CURRENCY_TYPE.ERC1155,
                        currency_identifier=id,
                        owner=self.to.with_prefix(),
                        change=value,
                    )
                )
        return changes
