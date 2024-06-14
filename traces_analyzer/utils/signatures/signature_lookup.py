from abc import ABC, abstractmethod

from traces_parser.datatypes import HexString


class SignatureLookup(ABC):
    @abstractmethod
    def lookup_by_hex(self, signature_hex: HexString) -> str | None:
        pass
