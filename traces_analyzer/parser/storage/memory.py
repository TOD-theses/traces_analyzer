from traces_analyzer.parser.storage.storage_value import HexStringStorageValue
from traces_analyzer.utils.hexstring import HexString


class Memory:
    def __init__(self) -> None:
        self._memory = HexString("")

    def get(self, offset: int, size: int) -> HexStringStorageValue:
        """Get memory range, offset and size in bytes. Return 0s if accessing out of range memory, without expanding"""
        offset = offset * 2
        size = size * 2
        slice = self._memory.without_prefix()[offset : offset + size]
        slice = slice.ljust(size, "0")
        return HexStringStorageValue(HexString(slice))

    def get_all(self) -> HexStringStorageValue:
        return self.get(0, self.size())

    def set(self, offset: int, value: HexStringStorageValue):
        if not value.get_hexstring():
            return
        data = value.get_hexstring().without_prefix()
        self.check_expansion(offset, len(data) // 2)
        mem = self._memory.without_prefix()
        self._memory = HexString(mem[: offset * 2] + data + mem[offset * 2 + len(data) :])

    def check_expansion(self, offset: int, size: int):
        if size == 0:
            return
        while self.size() < offset + size:
            self._expand()

    def _expand(self):
        self._memory = self._memory + "00" * 32

    def size(self) -> int:
        """Get size in bytes"""
        return len(self._memory) // 2
