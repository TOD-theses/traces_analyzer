from collections import defaultdict

from typing_extensions import override

from traces_analyzer.analysis.analyzer import SingleInstructionAnalyzer
from traces_analyzer.instructions import Instruction


class InstructionUsageAnalyzer(SingleInstructionAnalyzer):
    """Analyze which instructions are used in a trace"""

    def __init__(self) -> None:
        super().__init__()
        self.used_opcodes_per_contract: dict[str, set[int]] = defaultdict(lambda: set())

    @override
    def on_instruction(self, instruction: Instruction):
        contract_address = instruction.call_frame.address
        self.used_opcodes_per_contract[contract_address].add(instruction.opcode)
