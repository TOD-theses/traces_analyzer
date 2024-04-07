from itertools import zip_longest
from tests.conftest import make_instruction
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.parser.instructions import POP, PUSH0, SLOAD, op_from_class
from traces_analyzer.parser.events_parser import TraceEvent


def test_tod_source_analyzer():
    common_trace_events = [
        TraceEvent(0x1, op_from_class(PUSH0), [], 1, []),
        TraceEvent(0x2, op_from_class(SLOAD), ["0x0"], 1, []),
    ]

    trace_events_one = common_trace_events + [TraceEvent(0x3, op_from_class(POP), ["0x1234"], 1, [])]
    trace_events_two = common_trace_events + [TraceEvent(0x3, op_from_class(POP), ["0x5678"], 1, [])]
    instructions_one = [
        make_instruction(PUSH0),
        make_instruction(SLOAD, pc=2, stack=["0x1"], stack_after=["0x1234"]),
        make_instruction(POP, pc=3, stack=["0x1234"]),
    ]
    instructions_two = [
        make_instruction(PUSH0),
        make_instruction(SLOAD, pc=2, stack=["0x1"], stack_after=["0x5678"]),
        make_instruction(POP, pc=3, stack=["0x5678"]),
    ]

    analyzer = TODSourceAnalyzer()

    for instruction_one, instruction_two, event_one, event_two in zip_longest(
        instructions_one, instructions_two, trace_events_one, trace_events_two
    ):
        analyzer.on_instructions(instruction_one, instruction_two)

    tod_source = analyzer.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == op_from_class(SLOAD)
    assert tod_source.instruction_one.stack_outputs == ("0x1234",)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == op_from_class(SLOAD)
    assert tod_source.instruction_two.stack_outputs == ("0x5678",)
