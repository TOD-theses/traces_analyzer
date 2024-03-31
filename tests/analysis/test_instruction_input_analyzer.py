from itertools import zip_longest
from tests.conftest import TEST_ROOT_CALLFRAME, make_instruction
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.instructions import CALL, LOG1, POP, STOP


def test_instruction_input_analyzer():
    child_frame = CallFrame(TEST_ROOT_CALLFRAME, 2, "0xroot", "0xchild", "0xchild", False, None)

    first_call_value = "0x1000"
    second_call_value = "0x100000"

    first_trace = [
        make_instruction(),
        make_instruction(
            CALL, stack=list(reversed(["0x1234", "0xchild", first_call_value, "0x0", "0x0", "0x0", "0x0"]))
        ),
        make_instruction(STOP, call_frame=child_frame, depth=2),
    ]
    second_trace = [
        make_instruction(),
        make_instruction(
            CALL, stack=list(reversed(["0x1234", "0xchild", second_call_value, "0x0", "0x0", "0x0", "0x0"]))
        ),
        make_instruction(POP, call_frame=child_frame, depth=2),
        make_instruction(STOP, call_frame=child_frame, depth=2),
    ]

    # run analysis
    analyzer = InstructionInputAnalyzer()
    for a, b in zip_longest(first_trace, second_trace):
        analyzer.on_instructions(a, b)

    # check if it detected the different CALL values
    instruction_input_changes = analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    assert len(instruction_input_changes[0].stack_input_changes) == 1

    assert instruction_input_changes[0].address == TEST_ROOT_CALLFRAME.code_address
    assert len(instruction_input_changes[0].stack_input_changes) == 1
    assert instruction_input_changes[0].stack_input_changes[0].index == 2
    assert instruction_input_changes[0].stack_input_changes[0].first_value == first_call_value
    assert instruction_input_changes[0].stack_input_changes[0].second_value == second_call_value

    # check if it detected the additional POP instruction in the 2nd trace
    only_first_executions, only_second_executions = analyzer.get_instructions_only_executed_by_one_trace()
    assert only_first_executions == []
    assert len(only_second_executions) == 1
    assert only_second_executions[0].opcode == POP.opcode


def test_instruction_input_analyzer_reports_stack_differences():
    memory_one = "0000000011110000"
    memory_two = "0000000022220000"
    mem_offset = "0x4"
    mem_size = "0x2"
    common_stack = list(reversed(["0x0", "0xchild", "0x0", mem_offset, mem_size, "0x0", "0x0"]))

    analyzer = InstructionInputAnalyzer()
    analyzer.on_instructions(
        make_instruction(CALL, stack=common_stack, memory=memory_one),
        make_instruction(CALL, stack=common_stack, memory=memory_two),
    )

    # check if it detected the different CALL inputs
    instruction_input_changes = analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == CALL.opcode
    assert change.memory_input_change is not None
    assert change.memory_input_change.first_value == "1111"
    assert change.memory_input_change.second_value == "2222"


def test_instruction_input_analyzer_reports_log_changes():
    topic = "0x1234"
    memory_one = "0000000011110000"
    memory_two = "0000000022220000"
    mem_offset = "0x4"
    mem_size = "0x2"
    common_stack = list(reversed([mem_offset, mem_size, topic]))

    analyzer = InstructionInputAnalyzer()
    analyzer.on_instructions(
        make_instruction(LOG1, stack=common_stack, memory=memory_one),
        make_instruction(LOG1, stack=common_stack, memory=memory_two),
    )

    # check if it detected the different CALL inputs
    instruction_input_changes = analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == LOG1.opcode
    assert change.memory_input_change is not None
    assert change.memory_input_change.first_value == "1111"
    assert change.memory_input_change.second_value == "2222"
