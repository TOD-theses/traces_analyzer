from abc import ABC, abstractmethod

from traces_analyzer.instructions import Instruction


class TraceAnalyzer(ABC):
    pass


class TraceComparisonAnalyzer(ABC):
    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        pass


class TODSourceAnalyzer(TraceComparisonAnalyzer):
    """Analyze at which instruction the TOD first had an effect"""

    pass


class InstructionUsageAnalyzer(TraceAnalyzer):
    """Analyze which instructions are used in a trace"""

    pass
