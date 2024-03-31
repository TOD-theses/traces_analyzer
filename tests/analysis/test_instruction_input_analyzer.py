from itertools import zip_longest
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.instructions import CALL, STOP, Unknown
from traces_analyzer.preprocessing.instructions_parser import parse_instructions
from traces_analyzer.preprocessing.events_parser import TraceEvent, parse_events


def test_instruction_input_analyzer():
    dummy_event = TraceEvent(-1, -1, [], -1)
    root_frame = CallFrame(None, 1, "0xsender", "0xroot", "0xroot")
    child_frame = CallFrame(root_frame, 2, "0xroot", "0xchild", "0xchild")

    first_call_value = "0x1000"
    second_call_value = "0x100000"

    first_trace = [
        Unknown(TraceEvent(0, 0xAB, ["stack"], 0), dummy_event, root_frame),
        CALL(
            TraceEvent(1, 0xF1, list(reversed(["0x1234", "0xchild", first_call_value, "0x0", "0x0", "0x0", "0x0"])), 0),
            dummy_event,
            root_frame,
        ),
        STOP(dummy_event, dummy_event, child_frame),
    ]
    second_trace = [
        Unknown(TraceEvent(0, 0xAB, ["stack"], 0), dummy_event, root_frame),
        CALL(
            TraceEvent(
                1, 0xF1, list(reversed(["0x1234", "0xchild", second_call_value, "0x0", "0x0", "0x0", "0x0"])), 0
            ),
            dummy_event,
            root_frame,
        ),
        Unknown(TraceEvent(2, 0xEE, [], 1), dummy_event, child_frame),
        STOP(dummy_event, dummy_event, child_frame),
    ]

    # run analysis
    analyzer = InstructionInputAnalyzer()
    for a, b in zip_longest(first_trace, second_trace):
        analyzer.on_instructions(a, b)

    # check if it detected the different CALL values
    instruction_input_changes = analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    assert len(instruction_input_changes[0].stack_input_changes) == 1

    assert instruction_input_changes[0].address == "0xroot"
    assert len(instruction_input_changes[0].stack_input_changes) == 1
    assert instruction_input_changes[0].stack_input_changes[0].index == 2
    assert instruction_input_changes[0].stack_input_changes[0].first_value == first_call_value
    assert instruction_input_changes[0].stack_input_changes[0].second_value == second_call_value

    # check if it detected the additional Unkown(opcode=0xEE) instruction in the 2nd trace
    only_first_executions, only_second_executions = analyzer.get_instructions_only_executed_by_one_trace()

    assert len(only_first_executions) == 0
    assert len(only_second_executions) == 1
    assert only_second_executions[0].opcode == 0xEE


def test_instruction_input_analyzer_reports_stack_differences():
    memory_one = "0000000011110000"
    memory_two = "0000000022220000"
    mem_offset = "0x4"
    mem_size = "0x2"

    common_stack = list(reversed(["0x0", "0xchild", "0x0", mem_offset, mem_size, "0x0", "0x0"]))
    dummy_event = TraceEvent(-1, -1, [], -1)
    root_frame = CallFrame(None, 1, "0xsender", "0xroot", "0xroot")

    instruction_one = CALL(TraceEvent(1, CALL.opcode, common_stack, 1, memory_one), dummy_event, root_frame)
    instruction_two = CALL(TraceEvent(1, CALL.opcode, common_stack, 1, memory_two), dummy_event, root_frame)

    # run analysis
    analyzer = InstructionInputAnalyzer()
    for a, b in zip_longest([instruction_one], [instruction_two]):
        analyzer.on_instructions(a, b)

    # check if it detected the different CALL inputs
    instruction_input_changes = analyzer.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == CALL.opcode
    assert change.memory_input_change is not None
    assert change.memory_input_change.first_value == "1111"
    assert change.memory_input_change.second_value == "2222"
