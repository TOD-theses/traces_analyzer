from dataclasses import dataclass
from itertools import zip_longest

from traces_analyzer.features.feature_extractor import DoubleInstructionFeatureExtractor
from traces_parser.parser.environment.call_context_manager import CallTree
from traces_parser.parser.instructions.instruction import Instruction
from traces_parser.parser.instructions_parser import ParsedTransaction


@dataclass
class RunInfo:
    feature_extractors: list[DoubleInstructionFeatureExtractor]
    transactions: tuple[ParsedTransaction, ParsedTransaction]


class FeatureExtractionRunner:
    def __init__(self, run_info: RunInfo) -> None:
        self.feature_extractors = run_info.feature_extractors
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
        for feature_extractor in self.feature_extractors:
            feature_extractor.on_instructions(instructions[0], instructions[1])
