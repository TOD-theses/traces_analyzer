from collections import UserList
from collections.abc import Iterable

from traces_analyzer.utils.hexstring import HexString


class StorageByte:
    def __init__(self, byte: bytes, created_at_step_index: int) -> None:
        self._byte = byte
        self._created_at_step_index = created_at_step_index
        # self.touched_at_step_indexes: list[int] = []

    def __str__(self) -> str:
        return self._byte.decode("utf-8")

    def __repr__(self) -> str:
        return f'<{self._byte.decode("utf-8")},{self._created_at_step_index}>'


class StorageByteGroup(UserList[StorageByte]):
    def __init__(self, storage_bytes: Iterable[StorageByte] | None = None) -> None:
        super().__init__(storage_bytes)

    def get_hexstring(self) -> HexString:
        x: list[str] = [storage_byte._byte.decode("utf-8") for storage_byte in self.data]
        return HexString("".join(x))

    def depends_on_instruction_indexes(self) -> set[int]:
        return set(byte._created_at_step_index for byte in self)

    def split_by_dependencies(self) -> list["StorageByteGroup"]:
        if not (size := len(self)):
            return []
        groups: list["StorageByteGroup"] = []
        current_start_index = 0
        current_step_index = self[0]._created_at_step_index
        for i in range(size):
            if self[i]._created_at_step_index != current_step_index:
                groups.append(self[current_start_index:i])
                current_start_index = i
                current_step_index = self[i]._created_at_step_index
        if current_start_index < size:
            groups.append(self[current_start_index:])

        return groups

    @staticmethod
    def from_hexstring(hexstring: HexString, creation_step_index: int):
        storage_bytes = [StorageByte(b.encode("utf-8"), creation_step_index) for b in hexstring.iter_bytes()]
        return StorageByteGroup(storage_bytes)

    @staticmethod
    def deprecated_from_hexstring(hexstring: HexString) -> "StorageByteGroup":
        return StorageByteGroup.from_hexstring(hexstring, -1)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, StorageByteGroup) and self.get_hexstring() == value.get_hexstring()
