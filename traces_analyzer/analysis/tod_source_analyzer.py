from dataclasses import dataclass

from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.preprocessing.instructions import Instruction


@dataclass
class TODSource:
    found: bool
    instruction_one: Instruction
    instruction_two: Instruction


class TODSourceAnalyzer(DoubleTraceAnalyzer):
    """Analyze at which instruction the TOD first had an effect"""

    def __init__(self) -> None:
        super().__init__()
        self._tod_source_instructions: tuple[Instruction, Instruction] | None = None

    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        if self._tod_source_instructions:
            return

        if step.trace_events_one[0] != step.trace_events_two[0]:
            raise Exception(
                "Error at determining TOD source. "
                f"Events differed before source was determined: {step.trace_events_one[0]} {step.trace_events_two[0]}"
            )

        if step.trace_events_one[1] != step.trace_events_two[1]:
            self._tod_source_instructions = step.instruction_one, step.instruction_two

    def get_tod_source(self) -> TODSource:
        if not self._tod_source_instructions:
            return TODSource(found=False, instruction_one=None, instruction_two=None)  # type: ignore[arg-type]
        return TODSource(
            found=True,
            instruction_one=self._tod_source_instructions[0],
            instruction_two=self._tod_source_instructions[1],
        )
