from itertools import zip_longest
from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.preprocessing.instructions import POP, PUSH0, SLOAD
from traces_analyzer.preprocessing.instructions_parser import parse_instructions
from traces_analyzer.preprocessing.events_parser import TraceEvent, parse_events


def test_tod_source_analyzer():
    common_trace_events = [
        TraceEvent(0x1, PUSH0.opcode, [], 1, []),
        TraceEvent(0x2, SLOAD.opcode, ["0x0"], 1, []),
    ]

    trace_events_one = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x1234"], 1, [])]
    trace_events_two = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x5678"], 1, [])]
    instructions_one = parse_instructions(trace_events_one)
    instructions_two = parse_instructions(trace_events_two)

    analyzer = TODSourceAnalyzer()

    for instruction_one, instruction_two, event_one, event_two in zip_longest(
        instructions_one, instructions_two, trace_events_one, trace_events_two
    ):
        analyzer.on_analysis_step(AnalysisStepDoubleTrace(event_one, instruction_one, event_two, instruction_two))

    tod_source = analyzer.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.stack_outputs == ("0x1234",)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == SLOAD.opcode
    assert tod_source.instruction_two.stack_outputs == ("0x5678",)
