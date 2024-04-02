from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import (
    CALL,
    op_from_class,
)
from traces_analyzer.preprocessing.instructions_parser import parse_instructions


def test_parser_empty_events():
    assert list(parse_instructions([])) == []


def test_call_inputs_memory_parsing():
    stack = ["0x0", "0x4bb", "0x24", "0xb", "0x0", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x940f"]
    memory = "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"

    call_event = TraceEvent(pc=1234, op=op_from_class(CALL), stack=stack, memory=memory, depth=1)
    instructions = list(parse_instructions([call_event]))
    call_instruction = instructions[0]

    assert isinstance(call_instruction, CALL)
    assert call_instruction.memory_input == "2e1a7d4d000000000000000000000000000000000000000000000000016345785d8a0000"
