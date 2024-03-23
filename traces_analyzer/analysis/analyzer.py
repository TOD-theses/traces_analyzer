from abc import ABC, abstractmethod
from dataclasses import dataclass

from traces_analyzer.instructions import Instruction
from traces_analyzer.trace_reader import TraceEvent


@dataclass
class AnalysisStep:
    """Info about the current step and if available the next step"""

    trace_events_one: tuple[TraceEvent, TraceEvent | None]
    trace_events_two: tuple[TraceEvent, TraceEvent | None]

    instructions_one: Instruction
    instructions_two: Instruction


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
        first_events: tuple[TraceEvent, TraceEvent | None],
        second_events: tuple[TraceEvent, TraceEvent | None],
    ):
        """Hook each instruction of two traces and the current and next TraceEvents"""
        pass
