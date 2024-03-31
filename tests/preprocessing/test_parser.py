import pytest
from traces_analyzer.preprocessing.instructions import (
    CALL,
    CALLCODE,
    DELEGATECALL,
    POP,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
)
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions_parser import UnexpectedDepthChange, parse_instructions


def test_parser_empty_events():
    assert list(parse_instructions([])) == []


def test_call_frame_parsing():
    # a -> CALL -> b -> DELEGATECALL -> c -> STATICCALL -> d -> CALLCODE -> e
    # -> STOP -> RETURN -> REVERT -> SELFDESTRUCT
    def dummy_event_at_depth(depth: int):
        return TraceEvent(1234, POP.opcode, ["0x1122"], depth)

    addr = {
        "root": "0x1234123412341234123412341234123412341234",
        "call": "0x1111",
        "delegatecall": "0x2222",
        "staticcall": "0x3333",
        "callcode": "0x4444",
    }

    test_events = [
        dummy_event_at_depth(1),
        TraceEvent(1234, CALL.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", addr["call"], "0x0"], 1),
        dummy_event_at_depth(2),
        TraceEvent(1234, DELEGATECALL.opcode, ["0x0", "0x0", "0x0", "0x0", addr["delegatecall"], "0x0"], 2),
        dummy_event_at_depth(3),
        TraceEvent(1234, STATICCALL.opcode, ["0x0", "0x0", "0x0", "0x0", addr["staticcall"], "0x0"], 3),
        dummy_event_at_depth(4),
        TraceEvent(1234, CALLCODE.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", addr["callcode"], "0x0"], 4),
        TraceEvent(1234, STOP.opcode, [], 5),
        TraceEvent(1234, RETURN.opcode, [], 4),
        TraceEvent(1234, REVERT.opcode, [], 3),
        TraceEvent(1234, SELFDESTRUCT.opcode, [], 2),
        dummy_event_at_depth(1),
    ]

    instructions = list(parse_instructions(test_events))

    assert len(instructions) == 13

    def assert_code_addr(instruction_index: int, addr: str):
        assert instructions[instruction_index].call_frame.code_address == addr

    def assert_storage_addr(instruction_index: int, addr: str):
        assert instructions[instruction_index].call_frame.storage_address == addr

    # we start with the root address for both
    assert_code_addr(0, addr["root"])
    assert_storage_addr(0, addr["root"])

    # call instructions only modify the storage for the next instruction, no themselve
    assert_code_addr(1, addr["root"])
    assert_storage_addr(1, addr["root"])

    # CALL updates both
    assert_code_addr(2, addr["call"])
    assert_storage_addr(2, addr["call"])

    # DELEGATECALL only updates code, not storage
    assert_code_addr(4, addr["delegatecall"])
    assert_storage_addr(4, addr["call"])

    # STATICCALL updates both
    assert_code_addr(6, addr["staticcall"])
    assert_storage_addr(6, addr["staticcall"])

    # CALLCODE only updates code, not storage
    assert_code_addr(8, addr["callcode"])
    assert_storage_addr(8, addr["staticcall"])

    # STOP, RETURN, REVERT and SELFDESTRUCT all go to the parent callframe
    # code and storage addresses are as above
    # STOP
    assert_code_addr(9, addr["staticcall"])
    assert_storage_addr(9, addr["staticcall"])

    # RETURN
    assert_code_addr(10, addr["delegatecall"])
    assert_storage_addr(10, addr["call"])

    # REVERT
    assert_code_addr(11, addr["call"])
    assert_storage_addr(11, addr["call"])

    # SELFDESTRUCT
    assert_code_addr(12, addr["root"])
    assert_storage_addr(12, addr["root"])


def test_call_frame_updates_on_depth_change():
    call_target = "0x1111111111111111111111111111111111111111"

    test_events = [
        TraceEvent(1234, CALL.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", call_target, "0x0"], depth=1),
        TraceEvent(1235, POP.opcode, [], depth=2),
    ]

    instructions = list(parse_instructions(test_events))

    assert instructions[1].call_frame.code_address == call_target


def test_call_frame_does_not_update_with_same_depth():
    # this is necessary for CALLs to externally owned contracts which don't create a new context
    # and for precompiled contracts
    initial_code_addr = "0x1234123412341234123412341234123412341234"
    call_target = "0x1111111111111111111111111111111111111111"

    test_events = [
        TraceEvent(1234, CALL.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", call_target, "0x0"], depth=1),
        TraceEvent(1235, POP.opcode, [], depth=1),
    ]

    instructions = list(parse_instructions(test_events))

    assert instructions[1].call_frame.code_address == initial_code_addr


def test_call_frame_makes_exceptional_halt():
    # we assume an exceptional halt if the depth decreases by one
    initial_code_addr = "0x1234123412341234123412341234123412341234"
    call_target = "0x1111111111111111111111111111111111111111"

    test_events = [
        TraceEvent(1234, CALL.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", call_target, "0x0"], depth=1),
        TraceEvent(1234, POP.opcode, [], depth=2),
        TraceEvent(1235, POP.opcode, [], depth=1),
    ]

    instructions = list(parse_instructions(test_events))

    assert instructions[2].call_frame.code_address == initial_code_addr


def test_call_frame_parsing_throws_on_unexpected_depth_change():
    test_events = [
        TraceEvent(1234, POP.opcode, [], depth=1),
        TraceEvent(1235, POP.opcode, [], depth=2),
    ]

    with pytest.raises(UnexpectedDepthChange):
        list(parse_instructions(test_events))


def test_call_inputs_memory_parsing():
    stack = ["0x0", "0x4bb", "0x24", "0xb", "0x0", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x940f"]
    memory = "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"

    call_event = TraceEvent(pc=1234, op=CALL.opcode, stack=stack, memory=memory, depth=1)
    instructions = list(parse_instructions([call_event]))
    call_instruction = instructions[0]

    assert isinstance(call_instruction, CALL)
    assert call_instruction.memory_input == "2e1a7d4d000000000000000000000000000000000000000000000000016345785d8a0000"
