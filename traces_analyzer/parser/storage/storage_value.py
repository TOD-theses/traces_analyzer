from collections import UserList
from collections.abc import Iterable

from traces_analyzer.utils.hexstring import HexString


class StorageByte:
    def __init__(self, byte: bytes, created_at_step_index: int) -> None:
        self.byte = byte
        self.created_at_step_index = created_at_step_index
        # self.touched_at_step_indexes: list[int] = []

    def __str__(self) -> str:
        return self.byte.decode("utf-8")

    def __repr__(self) -> str:
        return f'<{self.byte.decode("utf-8")},{self.created_at_step_index}>'


class StorageByteGroup(UserList[StorageByte]):
    def __init__(self, storage_bytes: Iterable[StorageByte] | None = None) -> None:
        super().__init__(storage_bytes)

    def get_hexstring(self) -> HexString:
        x: list[str] = [storage_byte.byte.decode("utf-8") for storage_byte in self.data]
        return HexString("".join(x))

    @staticmethod
    def from_hexstring(hexstring: HexString, creation_step_index: int):
        storage_bytes = [StorageByte(b.encode("utf-8"), creation_step_index) for b in hexstring.iter_bytes()]
        return StorageByteGroup(storage_bytes)

    @staticmethod
    def deprecated_from_hexstring(hexstring: HexString) -> "StorageByteGroup":
        return StorageByteGroup.from_hexstring(hexstring, -1)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, StorageByteGroup) and self.get_hexstring() == value.get_hexstring()
