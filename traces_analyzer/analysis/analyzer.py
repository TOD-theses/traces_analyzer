from abc import ABC, abstractmethod

from traces_analyzer.instructions import Instruction
from traces_analyzer.trace_reader import TraceEvent


class TraceAnalyzer(ABC):
    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class TraceComparisonAnalyzer(ABC):
    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        """Hook each instruction of two traces"""
        pass


class TraceEventComparisonAnalyzer(ABC):
    @abstractmethod
    def on_trace_events_history(
        self,
        first_instruction: Instruction,
        second_instruction: Instruction,
        first_events: tuple[TraceEvent, TraceEvent],
        second_events: tuple[TraceEvent, TraceEvent],
    ):
        """Hook each instruction of two traces and the current and next TraceEvents"""
        pass
