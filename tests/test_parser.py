import os
from pathlib import Path

from pytest import fixture
from traces_analyzer.instructions import (
    CALL,
    SLOAD,
)
from traces_analyzer.trace_reader import read_trace_file
from traces_analyzer.parser import parse_events


@fixture
def sample_traces_path(request) -> Path:
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)
    return Path(test_dir).parent.parent / "sample_traces"


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
        trace_events = list(read_trace_file(trace_file))
        assert len(trace_events) == expected_trace_events

        instructions = list(parse_events(trace_events))
        assert len(instructions) == len(trace_events)

        calls = [instruction for instruction in instructions if isinstance(instruction, CALL)]
        assert len(calls) == expected_calls

        sloads = [instruction for instruction in instructions if isinstance(instruction, SLOAD)]
        assert len(sloads) == expected_sloads

        assert sloads[0].key == "0xd7a8b5b72b22ea76954784721def9efafa7df99d65b759e7d1b78f9ee0094fbc"
        assert sloads[0].result == "0x1"
