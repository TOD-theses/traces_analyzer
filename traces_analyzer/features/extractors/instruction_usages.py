from collections import defaultdict
from typing import Mapping

from typing_extensions import override

from traces_analyzer.features.feature_extractor import SingleInstructionFeatureExtractor
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.utils.hexstring import HexString


class InstructionUsagesFeatureExtractor(SingleInstructionFeatureExtractor):
    """Analyze which instructions are used in a trace"""

    def __init__(self) -> None:
        super().__init__()
        self._used_opcodes_per_contract: dict[HexString, set[int]] = defaultdict(
            lambda: set()
        )

    @override
    def on_instruction(self, instruction: Instruction):
        contract_address = instruction.call_context.code_address
        self._used_opcodes_per_contract[contract_address].add(instruction.opcode)

    def get_used_opcodes_per_contract(self) -> Mapping[HexString, set[int]]:
        return self._used_opcodes_per_contract
