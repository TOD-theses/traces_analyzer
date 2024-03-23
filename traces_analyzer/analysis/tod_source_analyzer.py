from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.instructions import Instruction


class TODSourceAnalyzer(DoubleTraceAnalyzer):
    """Analyze at which instruction the TOD first had an effect"""

    def __init__(self) -> None:
        super().__init__()
        self._tod_source_instructions: tuple[Instruction, Instruction] | None = None

    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        if self.found_tod_source():
            return

        if step.trace_events_one[0] != step.trace_events_two[0]:
            raise Exception(
                "Error at determining TOD source. "
                f"Events differed before source was determined: {step.trace_events_one[0]} {step.trace_events_two[0]}"
            )

        if step.trace_events_one[1] != step.trace_events_two[1]:
            self._tod_source_instructions = step.instruction_one, step.instruction_two

    def found_tod_source(self) -> bool:
        return self._tod_source_instructions is not None

    def get_tod_source(self) -> tuple[Instruction, Instruction] | None:
        return self._tod_source_instructions
