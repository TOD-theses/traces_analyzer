from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from typing_extensions import override

from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import Instruction


@dataclass
class AnalysisStepSingleTrace:
    """Info about the current step"""

    trace_event: TraceEvent | None
    instruction: Instruction


@dataclass
class AnalysisStepDoubleTrace:
    """Info about the current step and if available the next step"""

    trace_event_one: TraceEvent | None
    instruction_one: Instruction

    trace_event_two: TraceEvent | None
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
        single_step_one = AnalysisStepSingleTrace(trace_event=step.trace_event_one, instruction=step.instruction_one)
        single_step_two = AnalysisStepSingleTrace(trace_event=step.trace_event_two, instruction=step.instruction_one)

        # TODO: consider to only call these steps if the single steps are non-empty
        self.one.on_analysis_step(single_step_one)
        self.two.on_analysis_step(single_step_two)


class SingleInstructionAnalyzer(SingleTraceAnalyzer):
    def on_analysis_step(self, step: AnalysisStepSingleTrace):
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
            step.trace_event_one,
            step.trace_event_two,
        )

    @abstractmethod
    def on_trace_events_history(
        self,
        first_instruction: Instruction,
        second_instruction: Instruction,
        first_event: TraceEvent | None,
        second_event: TraceEvent | None,
    ):
        """Hook each instruction of two traces and the current and next TraceEvents"""
        pass
