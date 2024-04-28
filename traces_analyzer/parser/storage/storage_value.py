from abc import ABC, abstractmethod
from dataclasses import dataclass

from traces_analyzer.utils.hexstring import HexString


class StorageValue(ABC):

    @abstractmethod
    def get_hexstring(self) -> HexString:
        """The hexstring representation. May contain a leading 0x"""
        pass


@dataclass
class HexStringStorageValue(StorageValue):
    hexstring: HexString

    def get_hexstring(self) -> HexString:
        return self.hexstring
