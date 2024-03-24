from traces_analyzer.preprocessing.instructions import (
    CALL,
    CALLCODE,
    DELEGATECALL,
    POP,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    SLOAD,
    STATICCALL,
    STOP,
)
from traces_analyzer.preprocessing.events_parser import TraceEvent, parse_events
from traces_analyzer.preprocessing.instructions_parser import parse_instructions


def test_parse_traces(sample_traces_path):
    trace_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_attack"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )
    trace_path = trace_path.absolute()
    expected_trace_events = 3283
    expected_calls = 4
    expected_sloads = 23

    with open(trace_path) as trace_file:
        trace_events = list(parse_events(trace_file))
        assert len(trace_events) == expected_trace_events

        instructions = list(parse_instructions(trace_events))
        assert len(instructions) == len(trace_events)

        calls = [instruction for instruction in instructions if isinstance(instruction, CALL)]
        assert len(calls) == expected_calls
        assert calls[0].address == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        assert calls[0].value == "0x62884461f1460000"

        sloads = [instruction for instruction in instructions if isinstance(instruction, SLOAD)]
        assert len(sloads) == expected_sloads

        assert sloads[0].key == "0xd7a8b5b72b22ea76954784721def9efafa7df99d65b759e7d1b78f9ee0094fbc"
        assert sloads[0].result == "0x1"


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


def test_call_frame_ignores_precompiled_contracts():
    precompiled_contract_addr = "0x1"
    initial_code_addr = "0x1234123412341234123412341234123412341234"

    test_events = [
        TraceEvent(1234, CALL.opcode, ["0x0", "0x0", "0x0", "0x0", "0x0", precompiled_contract_addr, "0x0"], 1),
        TraceEvent(1235, POP.opcode, [], 1),
    ]

    instructions = list(parse_instructions(test_events))

    assert instructions[1].call_frame.code_address == initial_code_addr
