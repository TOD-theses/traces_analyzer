from dataclasses import dataclass
from itertools import tee, zip_longest
from typing import Iterable

from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace, DoubleTraceAnalyzer
from traces_analyzer.preprocessing.events_parser import parse_events
from traces_analyzer.preprocessing.instructions_parser import parse_instructions


@dataclass
class RunInfo:
    analyzers: list[DoubleTraceAnalyzer]
    traces_jsons: tuple[Iterable[str], Iterable[str]]


class AnalysisRunner:
    def __init__(self, run_info: RunInfo) -> None:
        self.analyzers = run_info.analyzers
        self.trace_one = run_info.traces_jsons[0]
        self.trace_two = run_info.traces_jsons[1]

    def run(self):
        trace_events_one = parse_events(self.trace_one)
        trace_events_two = parse_events(self.trace_two)

        # we use tee to copy the iterable so we can pass the copied iterable
        # to parse_instructions while still using the original iterable here
        # a more readable solution is likely to rewrite parse_instructions not to take an iterable
        trace_events_one, trace_events_one_copy = tee(trace_events_one)
        trace_events_two, trace_events_two_copy = tee(trace_events_two)

        instructions_one = parse_instructions(trace_events_one_copy)
        instructions_two = parse_instructions(trace_events_two_copy)

        current_event_one = next(trace_events_one)
        current_event_two = next(trace_events_two)

        # for both traces, take current instructions, and current+next trace events
        for instr_a, instr_b, next_event_one, next_event_two in zip_longest(
            instructions_one,
            instructions_two,
            trace_events_one,
            trace_events_two,
        ):
            self._process_step(
                AnalysisStepDoubleTrace(
                    trace_events_one=(current_event_one, next_event_one),
                    trace_events_two=(current_event_two, next_event_two),
                    instruction_one=instr_a,
                    instruction_two=instr_b,
                )
            )
            current_event_one = next_event_one
            current_event_two = next_event_two

    def _process_step(self, step: AnalysisStepDoubleTrace):
        for analyzer in self.analyzers:
            analyzer.on_analysis_step(step)
