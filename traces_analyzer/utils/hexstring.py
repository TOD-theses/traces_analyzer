from collections import UserString


class HexString(UserString):
    def __init__(self, value: str) -> None:
        super().__init__(value.removeprefix("0x").lower())

    def with_prefix(self) -> str:
        return "0x" + self.data

    def without_prefix(self) -> str:
        return self.data

    def as_int(self) -> int:
        return int(self.data, 16)

    def lsb(self) -> "HexString":
        """Return the (padded) least significant byte"""
        return self[-2:].rjust(2, ("0"))

    def __int__(self) -> int:
        return int(self.data, 16)

    @staticmethod
    def from_int(value: int) -> "HexString":
        return HexString(hex(value))
