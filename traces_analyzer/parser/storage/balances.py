from typing_extensions import Self, override

from traces_analyzer.parser.information_flow.constant_step_indexes import (
    SPECIAL_STEP_INDEXES,
)
from traces_analyzer.parser.storage.storage import CloneableStorage
from traces_analyzer.utils.hexstring import HexString


class InvalidAddressException(Exception):
    pass


class Balances(CloneableStorage):
    def __init__(self) -> None:
        super().__init__()
        # map address to step_index
        self._balances: dict[HexString, int] = {}

    def last_modified_at_step_index(self, addr: HexString) -> int:
        return self._balances.get(
            self._format_addr(addr), SPECIAL_STEP_INDEXES.PRESTATE
        )

    def modified_at_step_index(
        self, addr: HexString, modified_at_step_index: int
    ) -> None:
        self._balances[self._format_addr(addr)] = modified_at_step_index

    @override
    def clone(self) -> Self:
        new_balances = self.__class__()
        for address, step_index in self._balances.items():
            new_balances.modified_at_step_index(address, step_index)

        return new_balances

    @staticmethod
    def _format_addr(addr: HexString) -> HexString:
        if addr.size() != 20:
            raise InvalidAddressException(
                f"Tried to use address {addr} with length {addr.size()} for balance lookup"
            )
        return addr.lower()
