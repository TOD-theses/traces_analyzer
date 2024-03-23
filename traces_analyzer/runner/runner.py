from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable

from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.parser import parse_events
from traces_analyzer.trace_reader import read_trace_file


@dataclass
class RunInfo:
    analyzers: list[DoubleTraceAnalyzer]
    traces_jsons: tuple[Iterable[str], Iterable[str]]


class Runner:
    def __init__(self, run_info: RunInfo) -> None:
        self.analyzers = run_info.analyzers
        self.trace_one = run_info.traces_jsons[0]
        self.trace_two = run_info.traces_jsons[1]

    def run(self):
        # TODO: reimplement without parsing everything upfront
        # likely also requires a rethinking of parse_events, maybe make it a class instead
        # TODO: test how this covers the edge cases (eg if the last trace events are analyzed)

        trace_events_one = list(read_trace_file(self.trace_one))
        trace_events_two = list(read_trace_file(self.trace_two))

        instructions_one = parse_events(trace_events_one)
        instructions_two = parse_events(trace_events_two)

        # for both traces, take current instructions, and current+next trace events
        for instr_a, instr_b, events_a, events_b in zip_longest(
            instructions_one,
            instructions_two,
            zip_longest(trace_events_one, trace_events_one[1:]),
            zip_longest(trace_events_two, trace_events_two[1:]),
        ):
            self._process_step(
                AnalysisStepDoubleTrace(
                    trace_events_one=events_a,
                    trace_events_two=events_b,
                    instruction_one=instr_a,
                    instruction_two=instr_b,
                )
            )

    def _process_step(self, step: AnalysisStepDoubleTrace):
        for analyzer in self.analyzers:
            analyzer.on_analysis_step(step)
