from traces_analyzer.parser.storage.storage import Storage
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


class TransientStorageTables:
    """Handle transient storage of all addresses"""

    def __init__(self) -> None:
        self._tables: dict[HexString, dict[HexString, StorageByteGroup]] = {}

    def get(self, address: HexString, key: HexString) -> StorageByteGroup:
        if not (table := self._tables.get(address.as_address())):
            raise Exception(f"Tried to access transient storage at {address} with key {key}, but table does not exist")
        if not (val := table.get(key)):
            raise Exception(f"Tried to access transient storage at {address} with key {key}, but key does not exist")

        return val

    def set(self, address: HexString, key: HexString, value: StorageByteGroup) -> None:
        address = address.as_address()
        self._tables.setdefault(address, {})
        assert len(value) == 32
        self._tables[address][key] = value


class TransientStorage(Storage):
    def __init__(self) -> None:
        super().__init__()
        self._transient_storage_table = TransientStorageTables()

    def current(self) -> TransientStorageTables:
        return self._transient_storage_table
