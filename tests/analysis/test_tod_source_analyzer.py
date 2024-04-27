from itertools import zip_longest
from tests.conftest import make_instruction
from traces_analyzer.features.extractors.tod_source import TODSourceFeatureExtractor
from traces_analyzer.parser.instructions.instructions import POP, PUSH0, SLOAD
from traces_analyzer.parser.events_parser import TraceEvent


def test_tod_source_analyzer():
    common_trace_events = [
        TraceEvent(0x1, PUSH0.opcode, [], 1, []),
        TraceEvent(0x2, SLOAD.opcode, ["0x0"], 1, []),
    ]

    trace_events_one = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x1234"], 1, [])]
    trace_events_two = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x5678"], 1, [])]
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

    feature_extractor = TODSourceFeatureExtractor()

    for instruction_one, instruction_two, event_one, event_two in zip_longest(
        instructions_one, instructions_two, trace_events_one, trace_events_two
    ):
        feature_extractor.on_instructions(instruction_one, instruction_two)

    tod_source = feature_extractor.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.stack_outputs == ("1234",)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == SLOAD.opcode
    assert tod_source.instruction_two.stack_outputs == ("5678",)
