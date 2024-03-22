from collections import Counter
from dataclasses import dataclass

from typing_extensions import override

from traces_analyzer.analysis.analyzer import TraceComparisonAnalyzer
from traces_analyzer.instructions import Instruction, StackInstruction


@dataclass(frozen=True)
class InstructionKey:
    address: str
    program_counter: int
    opcode: int
    stack_inputs: tuple


class InstructionInputAnalyzer(TraceComparisonAnalyzer):
    """Analyze how the instruction inputs of two traces differ"""

    counter: Counter[InstructionKey] = Counter()

    @override
    def on_instructions(self, first_instruction: Instruction | None, second_instruction: Instruction | None):
        if isinstance(first_instruction, StackInstruction):
            key = to_key(first_instruction)
            self.counter.update([key])

            if self.counter[key] == 0:
                self.counter.pop(key)

        if isinstance(second_instruction, StackInstruction):
            key = to_key(second_instruction)
            self.counter.subtract([key])

            if self.counter[key] == 0:
                self.counter.pop(key)


def to_key(instruction: StackInstruction) -> InstructionKey:
    return InstructionKey(
        address=instruction.call_frame.address,
        program_counter=instruction.program_counter,
        opcode=instruction.opcode,
        stack_inputs=tuple(instruction.stack_inputs),
    )
