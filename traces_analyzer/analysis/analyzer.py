from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from typing_extensions import override

from traces_analyzer.parser.instruction import Instruction


class SingleInstructionAnalyzer(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class DoubleInstructionAnalyzer(ABC):
    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        """Hook each instruction of two traces"""
        pass


A = TypeVar("A", bound=SingleInstructionAnalyzer)


class SingleToDoubleInstructionAnalyzer(DoubleInstructionAnalyzer, Generic[A]):
    def __init__(self, analyzer_one: A, analyzer_two: A) -> None:
        super().__init__()

        self.one = analyzer_one
        self.two = analyzer_two

    @override
    def on_instructions(self, instruction_one: Instruction | None, instruction_two: Instruction | None):
        if instruction_one:
            self.one.on_instruction(instruction_one)
        if instruction_two:
            self.two.on_instruction(instruction_two)
