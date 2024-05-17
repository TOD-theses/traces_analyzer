from collections import UserString


class HexString(UserString):
    def __init__(self, value: str) -> None:
        value = value.removeprefix("0x")
        value = value.lower()
        value = value if len(value) % 2 == 0 else "0" + value
        super().__init__(value)

    def with_prefix(self) -> str:
        return "0x" + self.data

    def without_prefix(self) -> str:
        return self.data

    def as_int(self) -> int:
        return int(self.data, 16)

    def as_address(self) -> "HexString":
        return self.as_size(20)

    def as_size(self, n: int) -> "HexString":
        """Return 0-padded last n bytes"""
        if self.size() == n:
            return self
        if n == 0:
            return self[0:0]
        return self[-2 * n :].rjust(2 * n, "0")

    def size(self) -> int:
        """Size in bytes"""
        return len(self) // 2

    def __int__(self) -> int:
        return int(self.data, 16)

    @staticmethod
    def from_int(value: int) -> "HexString":
        return HexString(hex(value))
