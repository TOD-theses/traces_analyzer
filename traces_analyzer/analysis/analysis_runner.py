from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable

from traces_analyzer.analysis.analyzer import DoubleInstructionAnalyzer
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.call_frame_manager import CallFrameManager, CallTree
from traces_analyzer.preprocessing.events_parser import parse_events
from traces_analyzer.preprocessing.instruction import Instruction
from traces_analyzer.preprocessing.instructions_parser import parse_instructions


@dataclass
class RunInfo:
    analyzers: list[DoubleInstructionAnalyzer]
    traces_jsons: tuple[Iterable[str], Iterable[str]]
    sender: str
    to: str
    calldata: str


class AnalysisRunner:
    def __init__(self, run_info: RunInfo) -> None:
        self.analyzers = run_info.analyzers
        self._trace_one = run_info.traces_jsons[0]
        self._trace_two = run_info.traces_jsons[1]
        self._call_frame_manager_one = _setup_call_frame_manager(run_info.sender, run_info.to, run_info.calldata)
        self._call_frame_manager_two = _setup_call_frame_manager(run_info.sender, run_info.to, run_info.calldata)

    def run(self):
        trace_events_one = parse_events(self._trace_one)
        trace_events_two = parse_events(self._trace_two)

        instructions_one = parse_instructions(trace_events_one, self._call_frame_manager_one)
        instructions_two = parse_instructions(trace_events_two, self._call_frame_manager_two)

        for instruction_one, instruction_two in zip_longest(
            instructions_one,
            instructions_two,
        ):
            self._process_step(
                (
                    instruction_one,
                    instruction_two,
                )
            )

    def get_call_trees(self) -> tuple[CallTree, CallTree]:
        return self._call_frame_manager_one.get_call_tree(), self._call_frame_manager_two.get_call_tree()

    def _process_step(self, instructions: tuple[Instruction, Instruction]):
        for analyzer in self.analyzers:
            analyzer.on_instructions(instructions[0], instructions[1])


def _setup_call_frame_manager(sender: str, to: str, calldata: str) -> CallFrameManager:
    return CallFrameManager(
        CallFrame(
            parent=None,
            calldata=calldata,
            depth=1,
            msg_sender=sender,
            code_address=to,
            storage_address=to,
        )
    )
