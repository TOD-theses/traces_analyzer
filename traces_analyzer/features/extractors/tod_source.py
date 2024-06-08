from dataclasses import dataclass

from typing_extensions import override

from traces_analyzer.features.feature_extractor import DoulbeInstructionFeatureExtractor
from traces_analyzer.parser.information_flow.constant_step_indexes import (
    SPECIAL_STEP_INDEXES,
)
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
    def on_instructions(
        self,
        first_instruction: Instruction | None,
        second_instruction: Instruction | None,
    ):
        if self._tod_source_instructions:
            return

        if not first_instruction or not second_instruction:
            return

        # TODO: this does not work if both instructions depend on the prestate
        # but something else caused the write change (ie it is no TOD)
        if depends_on_prestate(first_instruction) and depends_on_prestate(
            second_instruction
        ):
            if first_instruction.get_writes() != second_instruction.get_writes():
                self._tod_source_instructions = first_instruction, second_instruction

    def get_tod_source(self) -> TODSource:
        if not self._tod_source_instructions:
            return TODSource(found=False, instruction_one=None, instruction_two=None)  # type: ignore[arg-type]
        return TODSource(
            found=True,
            instruction_one=self._tod_source_instructions[0],
            instruction_two=self._tod_source_instructions[1],
        )


def depends_on_prestate(instruction: Instruction):
    return any(
        step_index == SPECIAL_STEP_INDEXES.PRESTATE
        for step_index, _, _ in instruction.get_accesses().get_dependencies()
    )
