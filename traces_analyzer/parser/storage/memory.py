from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


class Memory:
    def __init__(self) -> None:
        self._memory = StorageByteGroup()

    def get(self, offset: int, size: int, step_index: int) -> StorageByteGroup:
        """Get memory range, offset and size in bytes.
        Return 0s belonging to step_index if accessing out of range memory, without expanding"""
        slice = self._memory[offset : offset + size]
        if len(slice) < size:
            slice += StorageByteGroup.from_hexstring(
                HexString("00" * (size - len(slice))), step_index
            )
        return slice

    def get_all(self) -> StorageByteGroup:
        return StorageByteGroup(self._memory)

    def set(self, offset: int, value: StorageByteGroup, step_index: int):
        if not value.get_hexstring():
            return
        self.check_expansion(offset, len(value), step_index)
        self._memory[offset : offset + len(value)] = value

    def check_expansion(self, offset: int, size: int, step_index: int):
        """Expand memory if offset + size would be out of bounds. Marks step_index as creator"""
        if size == 0:
            return
        while self.size() < offset + size:
            self._expand(step_index)

    def _expand(self, step_index: int):
        self._memory += StorageByteGroup.from_hexstring(
            HexString("00" * 32), step_index
        )

    def size(self) -> int:
        """Get size in bytes"""
        return len(self._memory)
