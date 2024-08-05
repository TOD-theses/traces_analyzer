from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from typing_extensions import override

from traces_parser.parser.instructions.instruction import Instruction


class SingleInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class DoubleInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instructions(
        self,
        normal_instruction: Instruction | None,
        reverse_instruction: Instruction | None,
    ):
        """Hook each instruction of two traces"""
        pass


A = TypeVar("A", bound=SingleInstructionFeatureExtractor)


class SingleToDoubleInstructionFeatureExtractor(
    DoubleInstructionFeatureExtractor, Generic[A]
):
    def __init__(self, feature_extractor_one: A, feature_extractor_two: A) -> None:
        super().__init__()

        self.normal = feature_extractor_one
        self.reverse = feature_extractor_two

    @override
    def on_instructions(
        self,
        normal_instruction: Instruction | None,
        reverse_instruction: Instruction | None,
    ):
        if normal_instruction:
            self.normal.on_instruction(normal_instruction)
        if reverse_instruction:
            self.reverse.on_instruction(reverse_instruction)
