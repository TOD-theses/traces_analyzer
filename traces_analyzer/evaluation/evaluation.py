from abc import ABC, abstractmethod


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
        return {
            "evaluation_type": self._type_key,
            "report": self._dict_report(),
        }

    def cli_report(self) -> str:
        return f"=== Evaluation: {self._type_name} ===\n{self._cli_report()}\n\n"

    @abstractmethod
    def _dict_report(self) -> dict:
        pass

    @abstractmethod
    def _cli_report(self) -> str:
        pass
