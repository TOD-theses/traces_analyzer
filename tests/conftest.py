from pytest import FixtureRequest, fixture
from pathlib import Path
import pytest
import sys

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instructions import JUMPDEST
from traces_analyzer.parser.instructions_parser import parse_instruction
from traces_analyzer.parser.environment.parsing_environment import ParsingEnvironment
from traces_analyzer.parser.environment.storage import MemoryValue


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


TEST_ROOT_CALLCONTEXT = CallContext(None, "", 1, "0x0", "0x0", "0x0", False, None)


def make_instruction(
    type: type[Instruction] = JUMPDEST,
    pc=1,
    step_index=0,
    stack=[],
    memory="",
    stack_after=[],
    memory_after="",
    call_context=TEST_ROOT_CALLCONTEXT,
):
    # TODO: directly create instruction instead of parsing inputs/outputs from stack
    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.current_step_index = step_index
    env.current_stack = stack
    env.current_call_context = call_context
    env.memory.set(0, MemoryValue(memory))
    return parse_instruction(env, type.opcode, pc, stack_after, memory_after)
