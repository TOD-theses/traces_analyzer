from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from typing_extensions import override

from traces_parser.parser.instructions.instruction import Instruction


class SingleInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class DoulbeInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instructions(
        self,
        first_instruction: Instruction | None,
        second_instruction: Instruction | None,
    ):
        """Hook each instruction of two traces"""
        pass


A = TypeVar("A", bound=SingleInstructionFeatureExtractor)


class SingleToDoubleInstructionFeatureExtractor(
    DoulbeInstructionFeatureExtractor, Generic[A]
):
    def __init__(self, feature_extractor_one: A, feature_extractor_two: A) -> None:
        super().__init__()

        self.one = feature_extractor_one
        self.two = feature_extractor_two

    @override
    def on_instructions(
        self,
        first_instruction: Instruction | None,
        second_instruction: Instruction | None,
    ):
        if first_instruction:
            self.one.on_instruction(first_instruction)
        if second_instruction:
            self.two.on_instruction(second_instruction)
