from traces_analyzer.parser.storage.address_key_storage import AddressKeyStorage
from traces_analyzer.parser.storage.storage import Storage


class PersistentStorage(Storage):
    def __init__(self) -> None:
        super().__init__()
        self._transient_storage_table = AddressKeyStorage()

    def current(self) -> AddressKeyStorage:
        return self._transient_storage_table
