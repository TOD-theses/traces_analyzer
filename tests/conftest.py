from pytest import FixtureRequest, fixture
from pathlib import Path
import pytest
import sys

from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.events_parser import TraceEvent
from traces_analyzer.preprocessing.instructions import JUMPDEST, Instruction, parse_instruction


@fixture
def root_dir(request: FixtureRequest) -> Path:
    return request.config.rootpath


@fixture
def sample_traces_path(root_dir: Path) -> Path:
    sample_traces_path = root_dir / "sample_traces"

    if not sample_traces_path.is_dir():
        pytest.skip("This test requires traces from sample_traces")

    return sample_traces_path


# each test runs on cwd to its temp dir
@fixture(autouse=True)
def go_to_tmpdir(request):
    # Get the fixture dynamically by its name.
    tmpdir = request.getfixturevalue("tmpdir")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmpdir))
    # Chdir only for the duration of the test.
    with tmpdir.as_cwd():
        yield


TEST_ROOT_CALLFRAME = CallFrame(None, 1, "0x0", "0x0", "0x0")


def make_instruction(
    type: type[Instruction] = JUMPDEST,
    pc=1,
    stack=[],
    depth=1,
    memory="",
    stack_after=[],
    memory_after="",
    depth_after=1,
    call_frame=TEST_ROOT_CALLFRAME,
):
    event = TraceEvent(pc, type.opcode, stack, depth, memory)
    next_event = TraceEvent(pc + 1, JUMPDEST.opcode, stack_after, depth_after, memory_after)
    return parse_instruction(event, next_event, call_frame)
