from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.instructions import CALL, STOP, Unknown
from traces_analyzer.preprocessing.events_parser import TraceEvent


def test_instruction_usage_analyzer():
    dummy_event = TraceEvent(-1, -1, [], -1)
    root_frame = CallFrame(None, 1, "0xsender", "0xroot", "0xroot")
    child_frame = CallFrame(root_frame, 2, "0xroot", "0xchild", "0xchild")

    trace = [
        Unknown(TraceEvent(0, 0xAA, ["stack"], 1), dummy_event, root_frame),
        Unknown(TraceEvent(1, 0xAB, ["stack"], 1), dummy_event, root_frame),
        CALL(
            TraceEvent(2, 0xF1, list(reversed(["0x1234", "0xchild", "0x1234", "0x0", "0x0", "0x0", "0x0"])), 1),
            dummy_event,
            root_frame,
        ),
        Unknown(TraceEvent(1, 0xAB, ["stack"], 1), dummy_event, child_frame),
        Unknown(TraceEvent(1, 0xAC, ["stack"], 1), dummy_event, child_frame),
        Unknown(TraceEvent(1, 0xAC, ["stack"], 1), dummy_event, child_frame),
        STOP(TraceEvent(3, 0x0, [], 2), dummy_event, child_frame),
    ]

    analyzer = InstructionUsageAnalyzer()
    for instruction in trace:
        analyzer.on_instruction(instruction)

    used_opcodes_per_contract = analyzer.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract["0xroot"] == {0xAA, 0xAB, 0xF1}
    assert used_opcodes_per_contract["0xchild"] == {0xAB, 0xAC, 0x0}
