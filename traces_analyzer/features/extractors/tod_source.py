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
    def on_instructions(
        self,
        first_instruction: Instruction | None,
        second_instruction: Instruction | None,
    ):
        if self._tod_source_instructions:
            return

        if not first_instruction or not second_instruction:
            # TODO: simply take previous instruction?
            raise Exception(
                "Instructions from one trace stopped before the TOD source was found"
            )

        if first_instruction.get_writes() != second_instruction.get_writes():
            self._tod_source_instructions = first_instruction, second_instruction
        elif first_instruction != second_instruction:
            self._tod_source_instructions = self._previous_instructions

        self._previous_instructions = (first_instruction, second_instruction)

    def get_tod_source(self) -> TODSource:
        if not self._tod_source_instructions:
            return TODSource(found=False, instruction_one=None, instruction_two=None)  # type: ignore[arg-type]
        return TODSource(
            found=True,
            instruction_one=self._tod_source_instructions[0],
            instruction_two=self._tod_source_instructions[1],
        )
