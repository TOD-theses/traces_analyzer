from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from typing_extensions import override

from traces_analyzer.parser.instructions.instruction import Instruction


class SingleInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class DoulbeInstructionFeatureExtractor(ABC):
    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        """Hook each instruction of two traces"""
        pass


A = TypeVar("A", bound=SingleInstructionFeatureExtractor)


class SingleToDoubleInstructionFeatureExtractor(DoulbeInstructionFeatureExtractor, Generic[A]):
    def __init__(self, feature_extractor_one: A, feature_extractor_two: A) -> None:
        super().__init__()

        self.one = feature_extractor_one
        self.two = feature_extractor_two

    @override
    def on_instructions(self, instruction_one: Instruction | None, instruction_two: Instruction | None):
        if instruction_one:
            self.one.on_instruction(instruction_one)
        if instruction_two:
            self.two.on_instruction(instruction_two)
