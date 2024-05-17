from typing_extensions import Self, override

from traces_analyzer.parser.storage.storage import CloneableStorage
from traces_analyzer.utils.hexstring import HexString

"""
BALANCE(addr) -> bytes32
SELFBALANCE() -> bytes32

TODO: implement the balance flow accesses/writes
CALL
CALLCODE
SELFDESTRUCT(addr)
"""


class InvalidAddressException(Exception):
    pass


class Balances(CloneableStorage):
    def __init__(self) -> None:
        super().__init__()
        # map address to step_index
        self._balances: dict[HexString, int] = {}

    def last_modified_at_step_index(self, addr: HexString) -> int:
        return self._balances.get(self._format_addr(addr), -1)

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
        if len(addr) != 40:
            raise InvalidAddressException(
                f"Tried to use address {addr} with length {len(addr) / 2} for balance lookup"
            )
        return addr.lower()
