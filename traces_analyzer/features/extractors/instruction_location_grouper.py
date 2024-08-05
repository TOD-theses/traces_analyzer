from collections import defaultdict
from typing import Iterable

from typing_extensions import override

from traces_analyzer.features.feature_extractor import SingleInstructionFeatureExtractor
from traces_parser.parser.instructions.instruction import Instruction
from traces_parser.datatypes import HexString

InstructionLocation = tuple[HexString, int]


class InstructionLocationsGrouperFeatureExtractor(SingleInstructionFeatureExtractor):
    """Extract a set of instructions and group them by location"""

    def __init__(self, instruction_opcodes: Iterable[int]) -> None:
        super().__init__()
        self._opcodes = set(instruction_opcodes)
        self.instruction_groups: dict[InstructionLocation, list[Instruction]] = (
            defaultdict(list)
        )

    @override
    def on_instruction(self, instruction: Instruction):
        if instruction.opcode not in self._opcodes:
            return
        location = (
            instruction.call_context.storage_address,
            instruction.program_counter,
        )
        self.instruction_groups[location].append(instruction)
