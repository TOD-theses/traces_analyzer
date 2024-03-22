from itertools import zip_longest
from traces_analyzer.analysis.InstructionInputAnalyzer import InstructionInputAnalyzer
from traces_analyzer.call_frame import CallFrame
from traces_analyzer.instructions import CALL, STOP, Unknown
from traces_analyzer.trace_reader import TraceEvent


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
        Unknown(dummy_event, dummy_event, child_frame),
        STOP(dummy_event, dummy_event, child_frame),
    ]
    analyzer = InstructionInputAnalyzer()
    for a, b in zip_longest(first_trace, second_trace):
        analyzer.on_instructions(a, b)

    assert len(analyzer.counter) == 2
    assert analyzer.counter.total() == 0

    # TODO: assert call values are correctly preserved
    # TODO: should this analyzer also cover missing instructions without inputs? eg Unknown?
