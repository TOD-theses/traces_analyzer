from tests.conftest import TEST_ROOT_CALLFRAME
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instruction_parser import parse_instruction

unknown_opcode = 0xF
dummy_event = TraceEvent(0x1, unknown_opcode, [], 1, None)
dummy_call_frame = TEST_ROOT_CALLFRAME


def test_instruction_parser_unknown():
    instruction = parse_instruction(TraceEvent(0x1, 0xF, [], 1, None), dummy_event, dummy_call_frame)

    assert instruction.opcode == 0xF
    assert instruction.name == "UNKNOWN"
    assert instruction.program_counter == 0x1
    assert instruction.stack_inputs == ()
    assert instruction.stack_outputs == ()
    assert instruction.memory_input == None
    assert instruction.memory_output == None
    assert instruction.call_frame == dummy_call_frame
    assert instruction.data == {}


def test_instruction_parser_call():
    gas = hex(0x1010)
    value = hex(0x1234)
    to = hex(0xAABB)
    memory = "0000000011110000"
    mem_offset = "0x4"
    mem_size = "0x2"
    stack = list(reversed([gas, to, value, mem_offset, mem_size, "0x0", "0x0"]))
    call_event = TraceEvent(0x1, 0xF1, stack, 1, memory)

    instruction = parse_instruction(call_event, dummy_event, dummy_call_frame)

    assert instruction.opcode == 0xF1
    assert instruction.name == "CALL"
    assert instruction.program_counter == 0x1
    assert instruction.stack_inputs == (gas, to, value, mem_offset, mem_size, "0x0", "0x0")
    assert instruction.stack_outputs == ()
    assert instruction.memory_input == "1111"
    assert instruction.memory_output == None
    assert instruction.call_frame == dummy_call_frame
    assert instruction.data == {"address": to, "input": "1111"}
