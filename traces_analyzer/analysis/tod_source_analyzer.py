from dataclasses import dataclass

from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.preprocessing.instruction import Instruction


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
        self._previous_instructions: tuple[Instruction, Instruction] | None = None

    def on_analysis_step(self, step: AnalysisStepDoubleTrace):
        if self._tod_source_instructions:
            return

        if not equal_outputs(step.instruction_one, step.instruction_two):
            self._tod_source_instructions = step.instruction_one, step.instruction_two
        elif step.instruction_one != step.instruction_two:
            self._tod_source_instructions = self._previous_instructions
            raise Exception(f"Missed the TOD source, unexpected unequal instructions: {step}")
        elif step.trace_event_one != step.trace_event_two:
            raise Exception(f"Missed the TOD source, unexpected unequal events: {step}")

        self._previous_instructions = (step.instruction_one, step.instruction_two)

    def get_tod_source(self) -> TODSource:
        if not self._tod_source_instructions:
            return TODSource(found=False, instruction_one=None, instruction_two=None)  # type: ignore[arg-type]
        return TODSource(
            found=True,
            instruction_one=self._tod_source_instructions[0],
            instruction_two=self._tod_source_instructions[1],
        )


def equal_inputs(instruction_one: Instruction, instruction_two: Instruction):
    return (
        instruction_one.stack_inputs == instruction_two.stack_inputs
        and instruction_one.memory_input == instruction_two.memory_input
    )


def equal_outputs(instruction_one: Instruction, instruction_two: Instruction):
    return (
        instruction_one.stack_outputs == instruction_two.stack_outputs
        and instruction_one.memory_output == instruction_two.memory_output
    )
