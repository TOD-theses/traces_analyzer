from traces_analyzer.preprocessing.instructions import (
    CALL,
    SLOAD,
)
from traces_analyzer.preprocessing.events_parser import parse_events
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
