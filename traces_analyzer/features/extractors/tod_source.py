from dataclasses import dataclass

from typing_extensions import override

from traces_analyzer.features.feature_extractor import DoulbeInstructionFeatureExtractor
from traces_analyzer.parser.instructions.instruction import Instruction


@dataclass
class TODSource:
    found: bool
    instruction_one: Instruction
    instruction_two: Instruction


class TODSourceFeatureExtractor(DoulbeInstructionFeatureExtractor):
    """Analyze at which instruction the TOD first had an effect"""

    def __init__(self) -> None:
        super().__init__()
        self._tod_source_instructions: tuple[Instruction, Instruction] | None = None
        self._previous_instructions: tuple[Instruction, Instruction] | None = None

    @override
    def on_instructions(self, instruction_one: Instruction | None, instruction_two: Instruction | None):
        if self._tod_source_instructions:
            return

        if not instruction_one or not instruction_two:
            # TODO: simply take previous instruction?
            raise Exception("Instructions from one trace stopped before the TOD source was found")

        if not equal_outputs(instruction_one, instruction_two):
            self._tod_source_instructions = instruction_one, instruction_two
        elif instruction_one != instruction_two:
            self._tod_source_instructions = self._previous_instructions

        self._previous_instructions = (instruction_one, instruction_two)

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
