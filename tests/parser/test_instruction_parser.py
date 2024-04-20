from tests.conftest import TEST_ROOT_CALLCONTEXT
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instructions_parser import parse_instruction
from traces_analyzer.parser.environment.parsing_environment import ParsingEnvironment
from traces_analyzer.parser.environment.storage import MemoryValue, StackValue

unknown_opcode = 0xF
dummy_event = TraceEvent(0x1, unknown_opcode, [], 1, None)
dummy_call_context = TEST_ROOT_CALLCONTEXT


def test_instruction_parser_unknown():
    env = ParsingEnvironment(dummy_call_context)
    instruction = parse_instruction(env, 0xF, 0x1, [], "")

    assert instruction.opcode == 0xF
    assert instruction.name == "UNKNOWN"
    assert instruction.program_counter == 0x1
    assert instruction.step_index == 0
    assert instruction.stack_inputs == ()
    assert instruction.stack_outputs == ()
    assert instruction.memory_input == None
    assert instruction.memory_output == None
    assert instruction.call_context == dummy_call_context
    assert instruction.get_data() == {}


def test_instruction_parser_call():
    gas = hex(0x1010)
    value = hex(0x1234)
    to = hex(0xAABB)
    mem_offset = "0x4"
    mem_size = "0x2"
    env = ParsingEnvironment(dummy_call_context)
    env.current_stack = list(reversed([gas, to, value, mem_offset, mem_size, "0x0", "0x0"]))
    env.stack.push(StackValue(reversed([gas, to, value, mem_offset, mem_size, "0x0", "0x0"])))
    env.memory.set(0, MemoryValue("0000000011110000"))

    instruction = parse_instruction(env, 0xF1, 0x1, [], "")

    assert instruction.opcode == 0xF1
    assert instruction.name == "CALL"
    assert instruction.program_counter == 0x1
    assert instruction.step_index == 0
    assert instruction.stack_inputs == (gas, to, value, mem_offset, mem_size, "0x0", "0x0")
    assert instruction.stack_outputs == ()
    assert instruction.memory_input == "1111"
    assert instruction.memory_output == None
    assert instruction.call_context == dummy_call_context
    assert instruction.get_data() == {"address": to, "input": "1111"}
