from itertools import zip_longest
from traces_analyzer.analysis.InstructionInputAnalyzer import InstructionInputAnalyzer
from traces_analyzer.call_frame import CallFrame
from traces_analyzer.instructions import CALL, STOP, Unknown
from traces_analyzer.parser import parse_events
from traces_analyzer.trace_reader import TraceEvent, read_trace_file


def test_instruction_input_analyzer():
    dummy_event = TraceEvent(-1, -1, [], -1)
    root_frame = CallFrame(None, 1, "0xsender", "0xroot")
    child_frame = CallFrame(root_frame, 2, "0xroot", "0xchild")

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
    assert len(instruction_input_changes[0].input_changes) == 1

    assert instruction_input_changes[0].address == "0xroot"
    assert len(instruction_input_changes[0].input_changes) == 1
    assert instruction_input_changes[0].input_changes[0].index == 2
    assert instruction_input_changes[0].input_changes[0].first_value == first_call_value
    assert instruction_input_changes[0].input_changes[0].second_value == second_call_value

    # check if it detected the additional Unkown(opcode=0xEE) instruction in the 2nd trace
    only_first_executions, only_second_executions = analyzer.get_instructions_only_executed_by_one_trace()

    assert len(only_first_executions) == 0
    assert len(only_second_executions) == 1
    assert only_second_executions[0].opcode == 0xEE


def test_instruction_input_analyzer_with_traces(sample_traces_path):
    trace_normal_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_normal"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )
    trace_attack_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_attack"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )

    with open(trace_normal_path) as trace_normal_file, open(trace_attack_path) as trace_attack_file:
        trace_normal_events = list(read_trace_file(trace_normal_file))
        trace_attack_events = list(read_trace_file(trace_attack_file))

        instructions_normal = list(parse_events(trace_normal_events))
        instructions_attack = list(parse_events(trace_attack_events))

        analyzer = InstructionInputAnalyzer()

        for a, b in zip_longest(instructions_normal, instructions_attack):
            analyzer.on_instructions(a, b)

        only_first_executions, only_second_executions = analyzer.get_instructions_only_executed_by_one_trace()
        assert len(only_first_executions) == 0
        assert len(only_second_executions) == 178  # the trace files differ exactly by 178 lines

        instruction_input_changes = analyzer.get_instructions_with_different_inputs()
        assert len(instruction_input_changes) == 0  # no instruction was called with different stack inputs
