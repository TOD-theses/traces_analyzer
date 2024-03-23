from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from typing_extensions import override

from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import Instruction


@dataclass
class AnalysisStepSingleTrace:
    """Info about the current step"""

    trace_events: tuple[TraceEvent, TraceEvent | None]
    instruction: Instruction


@dataclass
class AnalysisStepDoubleTrace:
    """Info about the current step and if available the next step"""

    trace_events_one: tuple[TraceEvent, TraceEvent | None]
    instruction_one: Instruction

    trace_events_two: tuple[TraceEvent, TraceEvent | None]
    instruction_two: Instruction


class SingleTraceAnalyzer(ABC):
    @abstractmethod
    def on_analysis_step(self, step: AnalysisStepSingleTrace):
        pass


class DoubleTraceAnalyzer(ABC):
    @abstractmethod
    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        pass


A = TypeVar("A", bound=SingleTraceAnalyzer)


class SingleToDoubleTraceAnalyzer(DoubleTraceAnalyzer, Generic[A]):
    def __init__(self, analyzer_one: A, analyzer_two: A) -> None:
        super().__init__()

        self.one = analyzer_one
        self.two = analyzer_two

    @override
    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        single_step_one = AnalysisStepSingleTrace(trace_events=step.trace_events_one, instruction=step.instruction_one)
        single_step_two = AnalysisStepSingleTrace(trace_events=step.trace_events_two, instruction=step.instruction_one)

        # TODO: consider to only call these steps if the single steps are non-empty
        self.one.on_analysis_step(single_step_one)
        self.two.on_analysis_step(single_step_two)


class SingleInstructionAnalyzer(SingleTraceAnalyzer):
    def on_analysis_step(self, step: AnalysisStepSingleTrace):
        # TODO: according to the types this should not be necessary
        # but probably for the last step it is called with None?
        if step.instruction:
            self.on_instruction(step.instruction)

    @abstractmethod
    def on_instruction(self, instruction: Instruction):
        """Hook each instruction of a single trace"""
        pass


class DoubleInstructionAnalyzer(DoubleTraceAnalyzer):
    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        self.on_instructions(step.instruction_one, step.instruction_two)

    @abstractmethod
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        """Hook each instruction of two traces"""
        pass


class TraceEventComparisonAnalyzer(DoubleTraceAnalyzer):
    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        self.on_trace_events_history(
            step.instruction_one,
            step.instruction_two,
            step.trace_events_one,
            step.trace_events_two,
        )

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
