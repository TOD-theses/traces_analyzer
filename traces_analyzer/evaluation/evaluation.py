from abc import ABC, abstractmethod
from typing import Any

from traces_parser.datatypes import HexString


class Evaluation(ABC):
    @property
    @abstractmethod
    def _type_name(self) -> str:
        pass

    @property
    @abstractmethod
    def _type_key(self) -> str:
        pass

    def dict_report(self) -> dict:
        report = {
            "evaluation_type": self._type_key,
            "report": self._dict_report(),
        }
        return _recursively_stringify_hexstrings(report)

    def cli_report(self) -> str:
        return f"=== Evaluation: {self._type_name} ===\n{self._cli_report()}\n\n"

    @abstractmethod
    def _dict_report(self) -> dict:
        pass

    @abstractmethod
    def _cli_report(self) -> str:
        pass


def _recursively_stringify_hexstrings(obj: Any) -> Any:
    if isinstance(obj, HexString):
        return obj.with_prefix()
    elif isinstance(obj, dict):
        new_dict = {}
        for key, val in obj.items():
            if isinstance(key, HexString):
                key = key.with_prefix()
            new_dict[key] = _recursively_stringify_hexstrings(val)
        return new_dict
    elif isinstance(obj, list):
        return [_recursively_stringify_hexstrings(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(_recursively_stringify_hexstrings(x) for x in obj)
    else:
        return obj
