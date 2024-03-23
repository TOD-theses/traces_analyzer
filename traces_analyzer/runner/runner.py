from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable

from traces_analyzer.analysis.analyzer import (
    AnalysisStep,
    TraceAnalyzer,
    TraceComparisonAnalyzer,
    TraceEventComparisonAnalyzer,
)
from traces_analyzer.parser import parse_events
from traces_analyzer.trace_reader import read_trace_file

AnalyzerType = TraceAnalyzer | TraceComparisonAnalyzer | TraceEventComparisonAnalyzer


@dataclass
class RunInfo:
    analyzers: list[AnalyzerType]
    traces_jsons: tuple[Iterable[str], Iterable[str]]


class Runner:
    def __init__(self, run_info: RunInfo) -> None:
        self.analyzers = run_info.analyzers
        self.trace_one = run_info.traces_jsons[0]
        self.trace_two = run_info.traces_jsons[1]

    def run(self):
        # TODO: reimplement without parsing everything upfront
        # likely also requires a rethinking of parse_events, maybe make it a class instead
        trace_events_one = list(read_trace_file(self.trace_one))
        trace_events_two = list(read_trace_file(self.trace_two))

        instructions_one = parse_events(trace_events_one)
        instructions_two = parse_events(trace_events_two)

        # for both traces, take current instructions, and current+next trace events
        # TODO: test how this covers the edge cases (eg if the last trace events are analyzed)
        for instr_a, instr_b, events_a, events_b in zip_longest(
            instructions_one,
            instructions_two,
            zip_longest(trace_events_one, trace_events_one[1:]),
            zip_longest(trace_events_two, trace_events_two[1:]),
        ):
            self._process_step(AnalysisStep(events_a, events_b, instr_a, instr_b))

    def _process_step(self, step: AnalysisStep):
        for analyzer in self.analyzers:
            analyze_step(analyzer, step)


def analyze_step(analyzer: AnalyzerType, step: AnalysisStep):
    # TODO: should we allow analyzers that only analyze a single trace? How do we implement this?
    # TODO: let the analyzer take the StepInfo instead
    if isinstance(analyzer, TraceComparisonAnalyzer):
        analyzer.on_instructions(step.instructions_one, step.instructions_two)
    elif isinstance(analyzer, TraceEventComparisonAnalyzer):
        analyzer.on_trace_events_history(
            step.instructions_one, step.instructions_two, step.trace_events_one, step.trace_events_two
        )
    else:
        raise Exception(f"Invalid analyzer type: {analyzer}")
