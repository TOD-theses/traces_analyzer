from abc import ABC, abstractmethod


class SignatureLookup(ABC):
    @abstractmethod
    def lookup_by_hex(self, signature_hex: str) -> str | None:
        pass
