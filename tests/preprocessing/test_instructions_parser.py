from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.call_frame_manager import CallFrameManager
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import (
    CALL,
    POP,
    op_from_class,
)
from traces_analyzer.preprocessing.instructions_parser import parse_instructions


def get_root_call_frame():
    return CallFrame(
        parent=None,
        depth=1,
        msg_sender="0x1111111111111111111111111111111111111111",
        code_address="0x1234123412341234123412341234123412341234",
        storage_address="0x1234123412341234123412341234123412341234",
        reverted=False,
        halt_type=None,
    )


def get_sample_call_frame_manager():
    return CallFrameManager(get_root_call_frame())


def test_parser_empty_events():
    assert list(parse_instructions([], get_sample_call_frame_manager())) == []


def test_call_inputs_memory_parsing():
    call_frame_manager = get_sample_call_frame_manager()
    stack = ["0x0", "0x4bb", "0x24", "0xb", "0x0", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x940f"]
    memory = "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"

    call_event = TraceEvent(pc=1234, op=op_from_class(CALL), stack=stack, memory=memory, depth=1)
    instructions = list(parse_instructions([call_event], call_frame_manager))
    call_instruction = instructions[0]

    assert isinstance(call_instruction, CALL)
    assert call_instruction.memory_input == "2e1a7d4d000000000000000000000000000000000000000000000000016345785d8a0000"


def test_parser_updates_call_frame_manager():
    root = get_root_call_frame()
    manager = CallFrameManager(root)
    call_target = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    stack = ["0x0", "0x4bb", "0x24", "0xb", "0x0", call_target, "0x940f"]
    memory = "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"

    events = [
        TraceEvent(pc=1, op=op_from_class(CALL), stack=stack, memory=memory, depth=1),
        TraceEvent(pc=2, op=op_from_class(POP), stack=["0x0"], memory="", depth=2),
    ]

    list(parse_instructions(events, manager))

    assert manager.get_current_call_frame() != root
    assert manager.get_current_call_frame().code_address == call_target
