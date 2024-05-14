from pytest import FixtureRequest, fixture
from pathlib import Path
import pytest
import sys

from tests.test_utils.test_utils import _test_call_context, _test_mem, _test_oracle, _test_stack, mock_env
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import JUMPDEST
from traces_analyzer.utils.mnemonics import opcode_to_name


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


TEST_ROOT_CALLCONTEXT = _test_call_context()


def make_instruction(
    type: type[Instruction] = JUMPDEST,
    pc=1,
    step_index=0,
    stack=_test_stack([]),
    memory=_test_mem(""),
    stack_after=[],
    memory_after="",
    call_context=TEST_ROOT_CALLCONTEXT,
):
    # TODO: directly create instruction instead of parsing inputs/outputs from stack
    env = mock_env(
        step_index=step_index,
        current_call_context=call_context,
    )
    env.stack = stack
    env.memory = memory
    oracle = _test_oracle(stack_after, memory_after)
    flow = type.parse_flow(env, oracle)
    return type(
        type.opcode,
        opcode_to_name(type.opcode) or "UnknownTestInstruction",
        pc,
        step_index,
        call_context,
        flow,
    )
