from dataclasses import dataclass

from typing_extensions import override

from traces_analyzer.features.feature_extractor import DoubleInstructionFeatureExtractor
from traces_parser.parser.information_flow.constant_step_indexes import (
    SPECIAL_STEP_INDEXES,
)
from traces_parser.parser.instructions.instruction import Instruction


@dataclass
class TODSource:
    found: bool
    instruction_one: Instruction
    instruction_two: Instruction


class TODSourceFeatureExtractor(DoubleInstructionFeatureExtractor):
    """Analyze at which instruction the TOD first had an effect"""

    def __init__(self) -> None:
        super().__init__()
        self._tod_source_instructions: tuple[Instruction, Instruction] | None = None
        self._previous_instructions: tuple[Instruction, Instruction] | None = None

    @override
    def on_instructions(
        self,
        normal_instruction: Instruction | None,
        reverse_instruction: Instruction | None,
    ):
        if self._tod_source_instructions:
            return

        if not normal_instruction or not reverse_instruction:
            return

        # TODO: this does not work if both instructions depend on the prestate
        # but something else caused the write change (ie it is no TOD)
        if depends_on_prestate(normal_instruction) and depends_on_prestate(
            reverse_instruction
        ):
            if normal_instruction.get_writes() != reverse_instruction.get_writes():
                self._tod_source_instructions = normal_instruction, reverse_instruction

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
