from abc import ABC, abstractmethod

from traces_analyzer.instructions import Instruction


class TraceAnalyzer(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        pass


class TraceComparisonAnalyzer(ABC):
    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        pass


class TODSourceAnalyzer(TraceComparisonAnalyzer):
    """Analyze at which instruction the TOD first had an effect"""

    pass
