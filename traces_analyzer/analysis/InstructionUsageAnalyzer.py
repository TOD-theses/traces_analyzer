from collections import defaultdict
from typing import Dict

from typing_extensions import override

from traces_analyzer.analysis.analyzer import TraceAnalyzer
from traces_analyzer.instructions import Instruction


class InstructionUsageAnalyzer(TraceAnalyzer):
    """Analyze which instructions are used in a trace"""

    used_opcodes_per_contract: Dict[str, set[int]] = defaultdict(lambda: set())

    @override
    def on_instruction(self, instruction: Instruction):
        contract_address = instruction.call_frame.address
        self.used_opcodes_per_contract[contract_address].add(instruction.opcode)
