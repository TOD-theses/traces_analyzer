from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


class AddressKeyStorage:
    """Handle storage of key-value pairs for any address"""

    def __init__(self) -> None:
        self._tables: dict[HexString, dict[HexString, StorageByteGroup]] = {}

    def knows_key(self, address: HexString, key: HexString) -> bool:
        """True if this key has explictly been previously set"""
        if not (table := self._tables.get(address.as_address())):
            return False
        if not table.get(key):
            return False
        return True

    def get(self, address: HexString, key: HexString) -> StorageByteGroup:
        if not self.knows_key(address, key):
            raise Exception(f"Tried to access storage at {address} with key {key}, but key or address is not known")

        return self._tables[address][key]

    def set(self, address: HexString, key: HexString, value: StorageByteGroup) -> None:
        address = address.as_address()
        self._tables.setdefault(address, {})
        assert len(value) == 32
        self._tables[address][key] = value
