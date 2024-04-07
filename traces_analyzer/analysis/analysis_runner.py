from dataclasses import dataclass
from itertools import zip_longest

from traces_analyzer.analysis.analyzer import DoubleInstructionAnalyzer
from traces_analyzer.parser.call_frame_manager import CallTree
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instructions_parser import ParsedTransaction


@dataclass
class RunInfo:
    analyzers: list[DoubleInstructionAnalyzer]
    transactions: tuple[ParsedTransaction, ParsedTransaction]


class AnalysisRunner:
    def __init__(self, run_info: RunInfo) -> None:
        self.analyzers = run_info.analyzers
        self.transaction_one = run_info.transactions[0]
        self.transaction_two = run_info.transactions[1]

    def run(self):
        for instruction_one, instruction_two in zip_longest(
            self.transaction_one.instructions,
            self.transaction_two.instructions,
        ):
            self._process_step(
                (
                    instruction_one,
                    instruction_two,
                )
            )

    def get_call_trees(self) -> tuple[CallTree, CallTree]:
        return self.transaction_one.call_tree, self.transaction_two.call_tree

    def _process_step(self, instructions: tuple[Instruction, Instruction]):
        for analyzer in self.analyzers:
            analyzer.on_instructions(instructions[0], instructions[1])
