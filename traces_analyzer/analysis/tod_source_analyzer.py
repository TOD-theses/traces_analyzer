from traces_analyzer.analysis.analyzer import TraceEventComparisonAnalyzer
from traces_analyzer.instructions import Instruction
from traces_analyzer.trace_reader import TraceEvent


class TODSourceAnalyzer(TraceEventComparisonAnalyzer):
    """Analyze at which instruction the TOD first had an effect"""

    def __init__(self) -> None:
        super().__init__()
        self._tod_source_instructions: tuple[Instruction, Instruction] | None = None

    def on_trace_events_history(
        self,
        first_instruction: Instruction,
        second_instruction: Instruction,
        first_events: tuple[TraceEvent, TraceEvent | None],
        second_events: tuple[TraceEvent, TraceEvent | None],
    ):
        if self.found_tod_source():
            return

        if first_events[0] != second_events[0]:
            raise Exception(
                "Error at determining TOD source. "
                f"Events differed before source was determined: {first_events[0]} {second_events[0]}"
            )

        if first_events[1] != second_events[1]:
            self._tod_source_instructions = first_instruction, second_instruction

    def found_tod_source(self) -> bool:
        return self._tod_source_instructions is not None

    def get_tod_source(self) -> tuple[Instruction, Instruction] | None:
        return self._tod_source_instructions
